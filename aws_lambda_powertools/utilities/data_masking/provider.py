from abc import abstractmethod
from collections.abc import Iterable

from aws_lambda_powertools.shared.constants import DATA_MASKING_STRING as MASK


class Provider:
    """
    When you try to create an instance of a subclass that does not implement the encrypt method,
    you will get a NotImplementedError with a message that says the method is not implemented:
    """

    @abstractmethod
    def encrypt(self, data):
        raise NotImplementedError("Subclasses must implement encrypt()")

    @abstractmethod
    def decrypt(self, data):
        raise NotImplementedError("Subclasses must implement decrypt()")

    def mask(self, data):
        if isinstance(data, (str, dict, bytes)):
            return MASK
        elif isinstance(data, Iterable):
            return type(data)([MASK] * len(data))
        return MASK
