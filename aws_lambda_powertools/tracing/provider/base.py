import abc
import numbers
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Sequence, Union


## TO-Discuss how to refactor this one. Segment seems X-ray exclusive concept
class BaseSpan(abc.ABC):
    """Holds common properties and methods on segment and subsegment."""

    @abc.abstractmethod
    def set_attribute(self, key: str, value: Union[str, numbers.Number, bool], **kwargs) -> None:
        """Annotate segment or subsegment with a key-value pair.

        Note: Annotations will be indexed for later search query.

        Parameters
        ----------
        key: str
            Metadata key
        value: Union[str, numbers.Number, bool]
            Annotation value
        """

    @abc.abstractmethod
    def record_exception(self, exception: BaseException, **kwargs):
        """Add an exception to trace entities.

        Parameters
        ----------
        exception: Exception
            Caught exception
            Output from `traceback.extract_stack()`.
        """


class BaseProvider(abc.ABC):
    @abc.abstractmethod
    @contextmanager
    def trace(self, name: str, **kwargs) -> Generator[BaseSpan, None, None]:
        """Return a span context manger.

        Parameters
        ----------
        name: str
            Span name
        kwargs: Optional[dict]
            Optional parameters to be propagated to span
        """

    @abc.abstractmethod
    @asynccontextmanager
    def trace_async(self, name: str, **kwargs) -> AsyncGenerator[BaseSpan, None]:
        """Return a async span context manger.

        Parameters
        ----------
        name: str
            Span name
        kwargs: Optional[dict]
            Optional parameters to be propagated to span
        """

    @abc.abstractmethod
    def set_attribute(self, key: str, value: Union[str, numbers.Number, bool], **kwargs) -> None:
        """Annotate current active trace entity with a key-value pair.

        Note: Annotations will be indexed for later search query.

        Parameters
        ----------
        key: str
            Metadata key
        value: Union[str, numbers.Number, bool]
            Annotation value
        """

    @abc.abstractmethod
    def patch(self, modules: Sequence[str]) -> None:
        """Instrument a set of supported libraries

        Parameters
        ----------
        modules: Set[str]
            Set of modules to be patched
        """

    @abc.abstractmethod
    def patch_all(self) -> None:
        """Instrument all supported libraries"""
