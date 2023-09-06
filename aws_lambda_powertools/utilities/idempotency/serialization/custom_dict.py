from typing import Any, Callable, Dict

from aws_lambda_powertools.utilities.idempotency.serialization.base import BaseIdempotencySerializer


class CustomDictSerializer(BaseIdempotencySerializer):
    def __init__(self, to_dict: Callable[[Any], Dict], from_dict: Callable[[Dict], Any]):
        """
        Parameters
        ----------
        to_dict: Callable[[Any], Dict]
            A function capable of transforming the saved data object representation into a dictionary
        from_dict: Callable[[Dict], Any]
            A function capable of transforming the saved dictionary into the original data object representation
        """
        self.__to_dict: Callable[[Any], Dict] = to_dict
        self.__from_dict: Callable[[Dict], Any] = from_dict

    def to_dict(self, data: Any) -> Dict:
        return self.__to_dict(data)

    def from_dict(self, data: Dict) -> Any:
        return self.__from_dict(data)
