from __future__ import annotations

import functools
import json
import logging
from typing import Any, Callable, Iterable, Optional, Union

from aws_lambda_powertools.utilities._data_masking.exceptions import (
    DataMaskingFieldNotFoundError,
    DataMaskingUnsupportedTypeError,
)
from aws_lambda_powertools.utilities._data_masking.provider import BaseProvider

logger = logging.getLogger(__name__)


class DataMasking:
    """
    Note: This utility is currently in a Non-General Availability (Non-GA) phase and may have limitations.
    Please DON'T USE THIS utility in production environments.
    Keep in mind that when we transition to General Availability (GA), there might be breaking changes introduced.

    The DataMasking class orchestrates masking, encrypting, and decrypting
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

        masked = masker.mask(data,fields=["sensitive"])

        return masked

    ```
    """

    def __init__(
        self,
        provider: Optional[BaseProvider] = None,
        json_serializer: Callable = functools.partial(json.dumps, ensure_ascii=False),
        json_deserializer: Callable = json.loads,
    ):
        self.provider = provider or BaseProvider()
        self.json_serializer = json_serializer
        self.json_deserializer = json_deserializer

    def encrypt(self, data, fields=None, **provider_options) -> str | dict:
        return self._apply_action(data, fields, self.provider.encrypt, **provider_options)

    def decrypt(self, data, fields=None, **provider_options) -> Any:
        return self._apply_action(data, fields, self.provider.decrypt, **provider_options)

    def mask(self, data, fields=None, **provider_options) -> str | Iterable:
        return self._apply_action(data, fields, self.provider.mask, **provider_options)

    def _apply_action(self, data: str | dict, fields, action: Callable, **provider_options):
        """
        Helper method to determine whether to apply a given action to the entire input data
        or to specific fields if the 'fields' argument is specified.

        Parameters
        ----------
        data : str | dict
            The input data to process.
        fields : Optional[List[any]] = None
            A list of fields to apply the action to. If 'None', the action is applied to the entire 'data'.
        action : Callable
           The action to apply to the data. It should be a callable that performs an operation on the data
           and returns the modified value.

        Returns
        -------
        any
            The modified data after applying the action.
        """

        if fields is not None:
            logger.debug(f"Running action {action.__name__} with fields {fields}")
            return self._apply_action_to_fields(data, fields, action, **provider_options)
        else:
            logger.debug(f"Running action {action.__name__} with the entire data")
            return action(data, **provider_options)

    def _apply_action_to_fields(
        self,
        data: Union[dict, str],
        fields: list,
        action: Callable,
        **provider_options,
    ) -> Union[dict, str]:
        """
        This method takes the input data, which can be either a dictionary or a JSON string,
        and applies a mask, an encryption, or a decryption to the specified fields.

        Parameters
        ----------
            data : Union[dict, str])
                The input data to process. It can be either a dictionary or a JSON string.
            fields : List
                A list of fields to apply the action to. Each field can be specified as a string or
                a list of strings representing nested keys in the dictionary.
            action : Callable
                The action to apply to the fields. It should be a callable that takes the current
                value of the field as the first argument and any additional arguments that might be required
                for the action. It performs an operation on the current value using the provided arguments and
                returns the modified value.
            **provider_options:
                Additional keyword arguments to pass to the 'action' function.

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
        new_dict = {'a': {'b': {'c': 'transformed_value'}}, 'x': {'y': 'transformed_value'}}
        ```
        """

        data_parsed: dict = self._normalize_data_to_parse(fields, data)

        for nested_field in fields:
            logger.debug(f"Processing nested field: {nested_field}")

            nested_parsed_field = nested_field

            # Ensure the nested field is represented as a string
            if not isinstance(nested_parsed_field, str):
                nested_parsed_field = self.json_serializer(nested_parsed_field)

            # Split the nested field into keys using dot, square brackets as separators
            # keys = re.split(r"\.|\[|\]", nested_field) # noqa ERA001 - REVIEW THIS

            keys = nested_parsed_field.replace("][", ".").replace("[", ".").replace("]", "").split(".")
            keys = [key for key in keys if key]  # Remove empty strings from the split

            # Traverse the dictionary hierarchy by iterating through the list of nested keys
            current_dict = data_parsed

            for key in keys[:-1]:
                # If enter here, the customer is passing potential list, set or tuple
                # Example "payload[0]"

                logger.debug(f"Processing {key} in field {nested_field}")

                # It supports dict, list, set and tuple
                try:
                    if isinstance(current_dict, dict) and key in current_dict:
                        # If enter heres, it captures the name of the key
                        # Example "payload"
                        current_dict = current_dict[key]
                    elif (
                        isinstance(current_dict, (set, tuple, list)) and key.isdigit() and int(key) < len(current_dict)
                    ):
                        # If enter heres, it captures the index of the key
                        # Example "[0]"
                        current_dict = current_dict[int(key)]
                except KeyError:
                    # Handle the case when the key doesn't exist
                    raise DataMaskingFieldNotFoundError(f"Key {key} not found in {current_dict}")

            last_key = keys[-1]

            current_dict = self._apply_action_to_specific_type(current_dict, action, last_key, **provider_options)

        return data_parsed

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

    def _apply_action_to_specific_type(self, current_dict: dict, action: Callable, last_key, **provider_options):
        logger.debug("Processing the last fields to apply the action")
        # Apply the action to the last key (either a specific index or dictionary key)
        if isinstance(current_dict, dict) and last_key in current_dict:
            current_dict[last_key] = action(current_dict[last_key], **provider_options)
        elif isinstance(current_dict, list) and last_key.isdigit() and int(last_key) < len(current_dict):
            current_dict[int(last_key)] = action(current_dict[int(last_key)], **provider_options)
        elif isinstance(current_dict, tuple) and last_key.isdigit() and int(last_key) < len(current_dict):
            index = int(last_key)
            current_dict = (
                current_dict[:index] + (action(current_dict[index], **provider_options),) + current_dict[index + 1 :]
            )
        elif isinstance(current_dict, set):
            # Convert the set to a list, apply the action, and convert back to a set
            elements_list = list(current_dict)
            elements_list[int(last_key)] = action(elements_list[int(last_key)], **provider_options)
            current_dict = set(elements_list)
        else:
            # Handle the case when the last key doesn't exist
            raise DataMaskingFieldNotFoundError(f"Key {last_key} not found in {current_dict}")

        return current_dict
