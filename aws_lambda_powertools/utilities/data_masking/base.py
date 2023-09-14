import json
from typing import Optional, Union

from aws_lambda_powertools.utilities.data_masking.provider import BaseProvider


class DataMasking:
    def __init__(self, provider: Optional[BaseProvider] = None):
        self.provider = provider or BaseProvider()

    def encrypt(self, data, fields=None, **provider_options):
        return self._apply_action(data, fields, self.provider.encrypt, **provider_options)

    def decrypt(self, data, fields=None, **provider_options):
        return self._apply_action(data, fields, self.provider.decrypt, **provider_options)

    def mask(self, data, fields=None, **provider_options):
        return self._apply_action(data, fields, self.provider.mask, **provider_options)

    def _apply_action(self, data, fields, action, **provider_options):
        """
        Helper method to determine whether to apply a given action to the entire input data
        or to specific fields if the 'fields' argument is specified.

        Parameters
        ----------
        data : any
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
            return self._apply_action_to_fields(data, fields, action, **provider_options)
        else:
            return action(data, **provider_options)

    def _apply_action_to_fields(self, data: Union[dict, str], fields: list,
                                action, **provider_options) -> Union[dict, str]:
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
            dict
                The modified dictionary after applying the action to the
            specified fields.

        Raises
        -------
            ValueError
                If 'fields' parameter is None.
            TypeError
                If the 'data' parameter is not a dictionary or a JSON string.

        # TODO: document for field in fields logic (more in code)
        Example
        -------
        >>> data = {'a': {'b': {'c': 1}}, 'x': {'y': 2}}
        >>> fields = ['a.b.c', 'a.x.y']
        The function will transform the value at 'a.b.c' (1) and 'a.x.y' (2)
        and store the result as:
        new_dict = {'a': {'b': {'c': 'transformed_value'}}, 'x': {'y': 'transformed_value'}}
        """

        if fields is None:
            raise ValueError("No fields specified.")

        if isinstance(data, str):
            # Parse JSON string as dictionary
            my_dict_parsed = json.loads(data)
        elif isinstance(data, dict):
            #TODO:  Revisit Turn into json string so everything has quotes around it.
            # Think this is only so integer keys work on str and vice versa?
            # so if we don't care abt that then can remove this

            # Turn into json string so everything has quotes around it
            my_dict_parsed = json.dumps(data)
            # Turn back into dict so can parse it
            my_dict_parsed = json.loads(my_dict_parsed)
        else:
            #TODO:  Revisit error handling in _apply_action_to_fields for string data that isn't a JSON string.
            # This is an internal method and can't be called by anything but just in case?
            # this method is only called if there's a list of fields, and if the list of
            # fields doesn't match the input data
            # then they get a key error, would that be enough?
            raise TypeError(
                "Unsupported data type. The 'data' parameter must be a dictionary or a JSON string "
                "representation of a dictionary.",
            )

        #TODO:  Revisit variable names in for field in fields to reduce cognitive load
        # is nested_key ok? field_path?
        for nested_key in fields:
            # Prevent overriding loop variable
            curr_nested_key = nested_key

            # this is also not necessary if we can ensure the list of fields will be a string
            # If the nested_key is not a string, convert it to a string representation
            if not isinstance(curr_nested_key, str):
                curr_nested_key = json.dumps(curr_nested_key)

            # Split the nested key string into a list of nested keys
            # ['a.b.c'] -> ['a', 'b', 'c']
            keys = curr_nested_key.split(".")

            # Initialize a current dictionary to the root dictionary
            curr_dict = my_dict_parsed

            # Traverse the dictionary hierarchy by iterating through the list of nested keys
            for key in keys[:-1]:
                curr_dict = curr_dict[key]

            # Retrieve the final value of the nested field
            valtochange = curr_dict[(keys[-1])]

            # Apply the specified 'action' to the target value
            curr_dict[keys[-1]] = action(valtochange, **provider_options)

        return my_dict_parsed
