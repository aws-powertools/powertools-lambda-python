from typing import Any, Callable, Dict

from aws_lambda_powertools.utilities.idempotency.serialization.base import BaseDictSerializer


class CustomDictSerializer(BaseDictSerializer):
    def __init__(self, to_dict: Callable[[Any], Dict], from_dict: Callable[[Dict], Any]):
        self.__to_dict: Callable[[Any], Dict] = to_dict
        self.__from_dict: Callable[[Dict], Any] = from_dict

    def to_dict(self, data: Any) -> Dict:
        return self.__to_dict(data)

    def from_dict(self, data: Dict) -> Any:
        return self.__from_dict(data)
