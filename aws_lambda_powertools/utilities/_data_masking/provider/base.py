import json
from typing import Any

from aws_lambda_powertools.utilities._data_masking.constants import DATA_MASKING_STRING


class BaseProvider:
    """
    When you try to create an instance of a subclass that does not implement the encrypt method,
    you will get a NotImplementedError with a message that says the method is not implemented:
    """

    def __init__(self, json_serializer=None, json_deserializer=None) -> None:
        self.json_serializer = json_serializer or self.default_json_serializer
        self.json_deserializer = json_deserializer or self.default_json_deserializer

    def default_json_serializer(self, data):
        return json.dumps(data).encode("utf-8")

    def default_json_deserializer(self, data):
        return json.loads(data.decode("utf-8"))

    def encrypt(self, data) -> str:
        raise NotImplementedError("Subclasses must implement encrypt()")

    def decrypt(self, data) -> Any:
        raise NotImplementedError("Subclasses must implement decrypt()")

    def mask(self, data) -> Any:
        if isinstance(data, (str, dict, bytes)):
            return DATA_MASKING_STRING
        elif isinstance(data, (list, tuple, set)):
            return type(data)([DATA_MASKING_STRING] * len(data))
        return DATA_MASKING_STRING
