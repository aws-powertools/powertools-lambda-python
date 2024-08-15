from abc import abstractmethod
from typing import IO, Generic

from aws_lambda_powertools.utilities.streaming.types import T


class BaseTransform(Generic[T]):
    """
    BaseTransform is the base class all data transformations need to implement.

    Parameters
    ----------
    transform_options: dict, optional
        Dictionary of options that can be passed to the underlying transformation to customize the behavior.
    """

    def __init__(self, **transform_options):
        self.transform_options = transform_options

    @abstractmethod
    def transform(self, input_stream: IO[bytes]) -> T:
        """
        Transforms the data from input_stream into an implementation of IO[bytes].

        This allows you to return your own object while still conforming to a protocol
        that allows transformations to be nested.
        """
        pass
