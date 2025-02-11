"""
Base class for Data Masking
!!! abstract "Usage Documentation"
    [`Data masking`](../../utilities/data_masking.md)
"""

from __future__ import annotations

import functools
import logging
import warnings
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence

from jsonpath_ng.ext import parse

from aws_lambda_powertools.utilities.data_masking.exceptions import (
    DataMaskingFieldNotFoundError,
    DataMaskingUnsupportedTypeError,
)
from aws_lambda_powertools.utilities.data_masking.provider import BaseProvider
from aws_lambda_powertools.warnings import PowertoolsUserWarning

if TYPE_CHECKING:
    from numbers import Number

logger = logging.getLogger(__name__)


class DataMasking:
    """
    The DataMasking class orchestrates erasing, encrypting, and decrypting
    for the base provider.

    Example
    -------
    ```python
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
        """
        Encrypt data using the configured encryption provider.

        Parameters
        ----------
        data : dict, Mapping, Sequence, or Number
            The data to encrypt.
        provider_options : dict, optional
            Provider-specific options for encryption.
        **encryption_context : str
            Additional key-value pairs for encryption context.

        Returns
        -------
        str
            The encrypted data as a base64-encoded string.

        Example
        --------

            encryption_provider = AWSEncryptionSDKProvider(keys=[KMS_KEY_ARN])
            data_masker = DataMasking(provider=encryption_provider)
            encrypted = data_masker.encrypt({"secret": "value"})
        """
        return self._apply_action(
            data=data,
            fields=None,
            action=self.provider.encrypt,
            provider_options=provider_options or {},
            dynamic_mask=None,
            custom_mask=None,
            regex_pattern=None,
            mask_format=None,
            **encryption_context,
        )

    def decrypt(
        self,
        data,
        provider_options: dict | None = None,
        **encryption_context: str,
    ) -> Any:
        """
        Decrypt data using the configured encryption provider.

        Parameters
        ----------
        data : dict, Mapping, Sequence, or Number
            The data to encrypt.
        provider_options : dict, optional
            Provider-specific options for encryption.
        **encryption_context : str
            Additional key-value pairs for encryption context.

        Returns
        -------
        str
            The encrypted data as a base64-encoded string.

        Example
        --------

            encryption_provider = AWSEncryptionSDKProvider(keys=[KMS_KEY_ARN])
            data_masker = DataMasking(provider=encryption_provider)
            encrypted = data_masker.decrypt(encrypted_data)
        """

        return self._apply_action(
            data=data,
            fields=None,
            action=self.provider.decrypt,
            provider_options=provider_options or {},
            dynamic_mask=None,
            custom_mask=None,
            regex_pattern=None,
            mask_format=None,
            **encryption_context,
        )

    def erase(
        self,
        data: Any,
        fields: list[str] | None = None,
        *,
        dynamic_mask: bool | None = None,
        custom_mask: str | None = None,
        regex_pattern: str | None = None,
        mask_format: str | None = None,
        masking_rules: dict | None = None,
    ) -> Any:
        """
        Erase or mask sensitive data in the input.

        Parameters
        ----------
        data : Any
            The data to be erased or masked.
        fields : list of str, optional
            List of field names to be erased or masked.
        dynamic_mask : bool, optional
            Whether to use dynamic masking.
        custom_mask : str, optional
            Custom mask to apply instead of the default.
        regex_pattern : str, optional
            Regular expression pattern for identifying data to mask.
        mask_format : str, optional
            Format string for the mask.
        masking_rules : dict, optional
            Dictionary of custom masking rules.

        Returns
        -------
        Any
            The data with sensitive information erased or masked.
        """
        if masking_rules:
            return self._apply_masking_rules(data=data, masking_rules=masking_rules)
        else:
            return self._apply_action(
                data=data,
                fields=fields,
                action=self.provider.erase,
                dynamic_mask=dynamic_mask,
                custom_mask=custom_mask,
                regex_pattern=regex_pattern,
                mask_format=mask_format,
            )

    def _apply_action(
        self,
        data,
        fields: list[str] | None,
        action: Callable,
        provider_options: dict | None = None,
        dynamic_mask: bool | None = None,
        custom_mask: str | None = None,
        regex_pattern: str | None = None,
        mask_format: str | None = None,
        **encryption_context: Any,
    ) -> Any:
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
                dynamic_mask=dynamic_mask,
                custom_mask=custom_mask,
                regex_pattern=regex_pattern,
                mask_format=mask_format,
            )
        else:
            logger.debug(f"Running action {action.__name__} with the entire data")
            if action.__name__ == "erase":
                return action(
                    data=data,
                    provider_options=provider_options,
                    dynamic_mask=dynamic_mask,
                    custom_mask=custom_mask,
                    regex_pattern=regex_pattern,
                    mask_format=mask_format,
                )
            else:
                return action(
                    data=data,
                    provider_options=provider_options,
                    **encryption_context,
                )

    def _apply_action_to_fields(
        self,
        data: dict | str,
        fields: list,
        action: Callable,
        provider_options: dict | None = None,
        dynamic_mask: bool | None = None,
        custom_mask: str | None = None,
        regex_pattern: str | None = None,
        mask_format: str | None = None,
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
        if not fields:
            raise ValueError("Fields parameter cannot be empty")

        data_parsed: dict = self._normalize_data_to_parse(data)

        # For in-place updates, json_parse accepts a callback function
        # this function must receive 3 args: field_value, fields, field_name
        # We create a partial callback to pre-populate known options (action, provider opts, enc ctx)
        update_callback = functools.partial(
            self._call_action,
            action=action,
            provider_options=provider_options,
            dynamic_mask=dynamic_mask,
            custom_mask=custom_mask,
            regex_pattern=regex_pattern,
            mask_format=mask_format,
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

            json_parse.update(
                data_parsed,
                lambda field_value, fields, field_name: update_callback(field_value, fields, field_name),  # type: ignore[misc] # noqa: B023
            )

        return data_parsed

    def _apply_masking_rules(self, data: dict, masking_rules: dict) -> dict:
        """
        Apply masking rules to data, supporting both simple field names and complex path expressions.

        Args:
            data: The dictionary containing data to mask
            masking_rules: Dictionary mapping field names or path expressions to masking rules

        Returns:
            dict: The masked data dictionary
        """
        result = deepcopy(data)

        for path, rule in masking_rules.items():
            try:
                jsonpath_expr = parse(f"$.{path}")
                matches = jsonpath_expr.find(result)

                if not matches:
                    warnings.warn(f"No matches found for path: {path}", stacklevel=2)
                    continue

                for match in matches:
                    try:
                        value = match.value
                        if value is not None:
                            masked_value = self.provider.erase(str(value), **rule)
                            match.full_path.update(result, masked_value)

                    except Exception as e:
                        warnings.warn(
                            f"Error masking value for path {path}: {str(e)}",
                            category=PowertoolsUserWarning,
                            stacklevel=2,
                        )
                        continue

            except Exception as e:
                warnings.warn(f"Error processing path {path}: {str(e)}", category=PowertoolsUserWarning, stacklevel=2)
                continue

        return result

    def _mask_nested_field(self, data: dict, field_path: str, mask_function):
        keys = field_path.split(".")
        current = data
        for key in keys[:-1]:
            current = current.get(key, {})
            if not isinstance(current, dict):
                return
        if keys[-1] in current:
            current[keys[-1]] = self.provider.erase(current[keys[-1]], **mask_function)

    @staticmethod
    def _call_action(
        field_value: Any,
        fields: dict[str, Any],
        field_name: str,
        action: Callable,
        provider_options: dict[str, Any] | None = None,
        dynamic_mask: bool | None = None,
        custom_mask: str | None = None,
        regex_pattern: str | None = None,
        mask_format: str | None = None,
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
        fields[field_name] = action(
            field_value,
            provider_options=provider_options,
            dynamic_mask=dynamic_mask,
            custom_mask=custom_mask,
            regex_pattern=regex_pattern,
            mask_format=mask_format,
            **encryption_context,
        )
        return fields[field_name]

    def _normalize_data_to_parse(self, data: str | dict) -> dict:
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
