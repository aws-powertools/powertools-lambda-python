import json
from typing import Union

from aws_lambda_powertools.utilities.data_masking.provider import Provider


class DataMasking:
    def __init__(self, provider=None):
        if provider is None:
            self.provider = Provider()
        else:
            self.provider = provider

    def encrypt(self, data, fields=None, **kwargs):
        return self._apply_action(data, fields, self.provider.encrypt, **kwargs)

    def decrypt(self, data, fields=None, **kwargs):
        return self._apply_action(data, fields, self.provider.decrypt, **kwargs)

    def mask(self, data, fields=None, **kwargs):
        return self._apply_action(data, fields, self.provider.mask, **kwargs)

    def _apply_action(self, data, fields, action, *args, **kwargs):
        if fields is not None:
            return self._use_ast(data, fields, action, *args, **kwargs)
        else:
            return action(data, *args, **kwargs)

    def _use_ast(self, data: Union[dict, str], fields, action, *args, **kwargs) -> str:
        if fields is None:
            raise ValueError("No fields specified.")
        if isinstance(data, str):
            # Parse JSON string as dictionary
            my_dict_parsed = json.loads(data)

        elif isinstance(data, dict):
            # Turn into json string so everything has quotes around it
            my_dict_parsed = json.dumps(data)
            # Turn back into dict so can parse it
            my_dict_parsed = json.loads(my_dict_parsed)
        else:
            raise TypeError(
                "Unsupported data type. The 'data' parameter must be a dictionary or a JSON string "
                "representation of a dictionary."
            )

        for field in fields:
            if not isinstance(field, str):
                field = json.dumps(field)
            keys = field.split(".")

            curr_dict = my_dict_parsed
            for key in keys[:-1]:
                curr_dict = curr_dict[key]
            valtochange = curr_dict[(keys[-1])]
            curr_dict[keys[-1]] = action(valtochange, *args, **kwargs)

        return my_dict_parsed
