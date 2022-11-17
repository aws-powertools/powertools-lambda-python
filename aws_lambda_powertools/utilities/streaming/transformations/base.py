from abc import abstractmethod
from typing import IO, Generic, TypeVar

T = TypeVar("T", bound=IO[bytes])


class BaseTransform(Generic[T]):
    """
    BaseTransform is the base class all data transformations need to implement.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    @abstractmethod
    def transform(self, input_stream: IO[bytes]) -> T:
        """
        Transforms the data from input_stream into an implementation of IO[bytes].

        This allows you to return your own object while still conforming to a protocol
        that allows transformations to be nested.
        """
        pass
