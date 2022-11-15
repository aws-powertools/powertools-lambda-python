import io
from abc import abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T", bound=io.RawIOBase)


class BaseTransform(Generic[T]):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    def transform(self, input_stream: io.RawIOBase) -> T:
        pass
