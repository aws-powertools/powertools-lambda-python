from __future__ import annotations

from typing import Any, Callable

from aws_lambda_powertools.utilities.idempotency.serialization.base import BaseIdempotencySerializer


class CustomDictSerializer(BaseIdempotencySerializer):
    def __init__(self, to_dict: Callable[[Any], dict], from_dict: Callable[[dict], Any]):
        """
        Parameters
        ----------
        to_dict: Callable[[Any], dict]
            A function capable of transforming the saved data object representation into a dictionary
        from_dict: Callable[[dict], Any]
            A function capable of transforming the saved dictionary into the original data object representation
        """
        self.__to_dict: Callable[[Any], dict] = to_dict
        self.__from_dict: Callable[[dict], Any] = from_dict

    def to_dict(self, data: Any) -> dict:
        return self.__to_dict(data)

    def from_dict(self, data: dict) -> Any:
        return self.__from_dict(data)
