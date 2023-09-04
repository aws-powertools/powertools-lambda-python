from abc import ABC
from collections.abc import Iterable
from typing import Union

from aws_lambda_powertools.utilities.data_masking.constants import DATA_MASKING_STRING


class BaseProvider(ABC):
    """
    When you try to create an instance of a subclass that does not implement the encrypt method,
    you will get a NotImplementedError with a message that says the method is not implemented:
    """

    def encrypt(self, data) -> Union[bytes, str]:
        raise NotImplementedError("Subclasses must implement encrypt()")

    def decrypt(self, data) -> any:
        raise NotImplementedError("Subclasses must implement decrypt()")

    def mask(self, data) -> str:
        if isinstance(data, (str, dict, bytes)):
            return DATA_MASKING_STRING
        elif isinstance(data, Iterable):
            return type(data)([DATA_MASKING_STRING] * len(data))
        return DATA_MASKING_STRING
