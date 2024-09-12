from __future__ import annotations

import functools
import logging
import warnings
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence, overload

from jsonpath_ng.ext import parse

from aws_lambda_powertools.utilities.data_masking.exceptions import (
    DataMaskingFieldNotFoundError,
    DataMaskingUnsupportedTypeError,
)
from aws_lambda_powertools.utilities.data_masking.provider import BaseProvider

if TYPE_CHECKING:
    from numbers import Number

logger = logging.getLogger(__name__)


class DataMasking:
    """
    The DataMasking class orchestrates erasing, encrypting, and decrypting
    for the base provider.

    Example:
    ```
    from aws_lambda_powertools.utilities.data_masking.base import DataMasking

    def lambda_handler(event, context):
        masker = DataMasking()

        data = {
            "project": "powertools",
            "sensitive": "password"
        }

        erased = masker.erase(data,fields=["sensitive"])

        return erased

    ```
    """

    def __init__(
        self,
        provider: BaseProvider | None = None,
        raise_on_missing_field: bool = True,
    ):
        self.provider = provider or BaseProvider()
        # NOTE: we depend on Provider to not confuse customers in passing the same 2 serializers in 2 places
        self.json_serializer = self.provider.json_serializer
        self.json_deserializer = self.provider.json_deserializer
        self.raise_on_missing_field = raise_on_missing_field

    def encrypt(
        self,
        data: dict | Mapping | Sequence | Number,
        provider_options: dict | None = None,
        **encryption_context: str,
    ) -> str:
        return self._apply_action(
            data=data,
            fields=None,
            action=self.provider.encrypt,
            provider_options=provider_options or {},
            **encryption_context,
        )

    def decrypt(
        self,
        data,
        provider_options: dict | None = None,
        **encryption_context: str,
    ) -> Any:
        return self._apply_action(
            data=data,
            fields=None,
            action=self.provider.decrypt,
            provider_options=provider_options or {},
            **encryption_context,
        )

    @overload
    def erase(self, data, fields: None) -> str: ...

    @overload
    def erase(self, data: list, fields: list[str]) -> list[str]: ...

    @overload
    def erase(self, data: tuple, fields: list[str]) -> tuple[str]: ...

    @overload
    def erase(self, data: dict, fields: list[str]) -> dict: ...

    def erase(self, data: Sequence | Mapping, fields: list[str] | None = None) -> str | list[str] | tuple[str] | dict:
        return self._apply_action(data=data, fields=fields, action=self.provider.erase)

    def _apply_action(
        self,
        data,
        fields: list[str] | None,
        action: Callable,
        provider_options: dict | None = None,
        **encryption_context: str,
    ):
        """
        Helper method to determine whether to apply a given action to the entire input data
        or to specific fields if the 'fields' argument is specified.

        Parameters
        ----------
        data : str | dict
            The input data to process.
        fields : list[str] | None
            A list of fields to apply the action to. If 'None', the action is applied to the entire 'data'.
        action : Callable
            The action to apply to the data. It should be a callable that performs an operation on the data
            and returns the modified value.
        provider_options : dict
            Provider specific keyword arguments to propagate; used as an escape hatch.
        encryption_context: str
            Encryption context to use in encrypt and decrypt operations.

        Returns
        -------
        any
            The modified data after applying the action.
        """

        if fields is not None:
            logger.debug(f"Running action {action.__name__} with fields {fields}")
            return self._apply_action_to_fields(
                data=data,
                fields=fields,
                action=action,
                provider_options=provider_options,
                **encryption_context,
            )
        else:
            logger.debug(f"Running action {action.__name__} with the entire data")
            return action(data=data, provider_options=provider_options, **encryption_context)

    def _apply_action_to_fields(
        self,
        data: dict | str,
        fields: list,
        action: Callable,
        provider_options: dict | None = None,
        **encryption_context: str,
    ) -> dict | str:
        """
        This method takes the input data, which can be either a dictionary or a JSON string,
        and erases, encrypts, or decrypts the specified fields.

        Parameters
        ----------
            data : dict | str)
                The input data to process. It can be either a dictionary or a JSON string.
            fields : list
                A list of fields to apply the action to. Each field can be specified as a string or
                a list of strings representing nested keys in the dictionary.
            action : Callable
                The action to apply to the fields. It should be a callable that takes the current
                value of the field as the first argument and any additional arguments that might be required
                for the action. It performs an operation on the current value using the provided arguments and
                returns the modified value.
            provider_options : dict
                Optional dictionary representing additional options for the action.
            **encryption_context: str
                Additional keyword arguments collected into a dictionary.

        Returns
        -------
            dict | str
                The modified dictionary or string after applying the action to the
            specified fields.

        Raises
        -------
            ValueError
                If 'fields' parameter is None.
            TypeError
                If the 'data' parameter is not a traversable type

        Example
        -------
        ```python
        >>> data = {'a': {'b': {'c': 1}}, 'x': {'y': 2}}
        >>> fields = ['a.b.c', 'a.x.y']
        # The function will transform the value at 'a.b.c' (1) and 'a.x.y' (2)
        # and store the result as:
        new_dict = {'a': {'b': {'c': '*****'}}, 'x': {'y': '*****'}}
        ```
        """

        data_parsed: dict = self._normalize_data_to_parse(fields, data)

        # For in-place updates, json_parse accepts a callback function
        # this function must receive 3 args: field_value, fields, field_name
        # We create a partial callback to pre-populate known options (action, provider opts, enc ctx)
        update_callback = functools.partial(
            self._call_action,
            action=action,
            provider_options=provider_options,
            **encryption_context,  # type: ignore[arg-type]
        )

        # Iterate over each field to be parsed.
        for field_parse in fields:
            # Parse the field expression using a 'parse' function.
            json_parse = parse(field_parse)
            # Find the corresponding keys in the normalized data using the parsed expression.
            result_parse = json_parse.find(data_parsed)

            if not result_parse:
                if self.raise_on_missing_field:
                    # If the data for the field is not found, raise an exception.
                    raise DataMaskingFieldNotFoundError(f"Field or expression {field_parse} not found in {data_parsed}")
                else:
                    # If the data for the field is not found, warning.
                    warnings.warn(f"Field or expression {field_parse} not found in {data_parsed}", stacklevel=2)

            # For in-place updates, json_parse accepts a callback function
            # that receives 3 args: field_value, fields, field_name
            # We create a partial callback to pre-populate known provider options (action, provider opts, enc ctx)
            update_callback = functools.partial(
                self._call_action,
                action=action,
                provider_options=provider_options,
                **encryption_context,  # type: ignore[arg-type]
            )

            json_parse.update(
                data_parsed,
                lambda field_value, fields, field_name: update_callback(field_value, fields, field_name),  # type: ignore[misc] # noqa: B023
            )

        return data_parsed

    @staticmethod
    def _call_action(
        field_value: Any,
        fields: dict[str, Any],
        field_name: str,
        action: Callable,
        provider_options: dict[str, Any] | None = None,
        **encryption_context,
    ) -> None:
        """
        Apply a specified action to a field value and update the fields dictionary.

        Params:
        --------
        - field_value: Current value of the field being processed.
        - fields: Dictionary representing the fields being processed (mutable).
        - field_name: Name of the field being processed.
        - action: Callable (function or method) to be applied to the field_value.
        - provider_options: Optional dictionary representing additional options for the action.
        - **encryption_context: Additional keyword arguments collected into a dictionary.

        Returns:
        - fields[field_name]: Returns the processed field value
        """
        fields[field_name] = action(field_value, provider_options=provider_options, **encryption_context)
        return fields[field_name]

    def _normalize_data_to_parse(self, fields: list, data: str | dict) -> dict:
        if not fields:
            raise ValueError("No fields specified.")

        if isinstance(data, str):
            # Parse JSON string as dictionary
            data_parsed = self.json_deserializer(data)
        elif isinstance(data, dict):
            # Convert the data to a JSON string in case it contains non-string keys (e.g., ints)
            # Parse the JSON string back into a dictionary
            data_parsed = self.json_deserializer(self.json_serializer(data))
        else:
            raise DataMaskingUnsupportedTypeError(
                f"Unsupported data type. Expected a traversable type (dict or str), but got {type(data)}.",
            )

        return data_parsed
