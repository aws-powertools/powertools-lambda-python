import abc
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Generator, Sequence


class BaseSpan(abc.ABC):
    """A span represents a unit of work or operation within a trace.
    Spans are the building blocks of Traces."""

    @abc.abstractmethod
    def set_attribute(self, key: str, value: Any, **kwargs) -> None:
        """Set an attribute for a span with a key-value pair.

        Parameters
        ----------
        key: str
            Attribute key
        value: Any
            Attribute value
        kwargs: Optional[dict]
            Optional parameters
        """

    @abc.abstractmethod
    def record_exception(self, exception: BaseException, **kwargs):
        """Records an exception to this Span.

        Parameters
        ----------
        exception: Exception
            Caught exception during the exectution of this Span
        kwargs: Optional[dict]
            Optional parameters
        """


class BaseProvider(abc.ABC):
    """BaseProvider is an abstract base class that defines the expected behavior for tracing providers
    used by Tracer. Inheriting classes must implement this interface to be compatible with Tracer.
    """

    @abc.abstractmethod
    @contextmanager
    def trace(self, name: str, **kwargs) -> Generator[BaseSpan, None, None]:
        """Context manager for creating a new span and set it
        as the current span in this tracer's context.

        Exiting the context manager will call the span's end method,
        as well as return the current span to its previous value by
        returning to the previous context.

        Parameters
        ----------
        name: str
            Span name
        kwargs: Optional[dict]
            Optional parameters to be propagated to the span
        """

    @abc.abstractmethod
    @asynccontextmanager
    def trace_async(self, name: str, **kwargs) -> AsyncGenerator[BaseSpan, None]:
        """Async Context manager for creating a new span and set it
        as the current span in this tracer's context.

        Exiting the context manager will call the span's end method,
        as well as return the current span to its previous value by
        returning to the previous context.

        Parameters
        ----------
        name: str
            Span name
        kwargs: Optional[dict]
            Optional parameters to be propagated to the span
        """

    @abc.abstractmethod
    def set_attribute(self, key: str, value: Any, **kwargs) -> None:
        """set attribute on current active span with a key-value pair.

        Parameters
        ----------
        key: str
            attribute key
        value: Any
            attribute value
        kwargs: Optional[dict]
            Optional parameters to be propagated to the span
        """

    @abc.abstractmethod
    def patch(self, modules: Sequence[str]) -> None:
        """Instrument a set of given libraries if supported by provider
        See specific provider for more detail

        Exmaple
        -------
        tracer = Tracer(service="payment")
        libraries = (['aioboto3',mysql])
        # provider.patch will be called by tracer.patch
        tracer.patch(libraries)

        Parameters
        ----------
        modules: Set[str]
            Set of modules to be patched
        """

    @abc.abstractmethod
    def patch_all(self) -> None:
        """Instrument all supported libraries"""
