import contextlib
import functools
import inspect
import logging
import os
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Callable, Generator, Optional, Sequence, Union, cast, overload

from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import resolve_truthy_env_var_choice, sanitize_xray_segment_name
from aws_lambda_powertools.shared.types import AnyCallableT
from aws_lambda_powertools.tracing.base import BaseSegment

logger = logging.getLogger(__name__)


is_cold_start = True


class BaseSpan(ABC):
    """A span represents a unit of work or operation within a trace.
    Spans are the building blocks of Traces."""

    @abstractmethod
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

    @abstractmethod
    def record_exception(self, exception: BaseException, **kwargs):
        """Records an exception to this Span.

        Parameters
        ----------
        exception: Exception
            Caught exception during the exectution of this Span
        kwargs: Optional[dict]
            Optional parameters
        """


class BaseProvider(ABC):
    """BaseProvider is an abstract base class that defines the expected behavior for tracing providers
    used by Tracer. Inheriting classes must implement this interface to be compatible with Tracer.
    """

    def __init__(self, service: str = ""):
        self.service = service

    @abstractmethod
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

    @abstractmethod
    @asynccontextmanager
    def trace_async(self, name: str, **kwargs) -> AsyncGenerator[BaseSpan, None]:
        """Async Context manager for creating a new span async and set it
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
    def patch_all(self) -> None:
        """Instrument all supported libraries"""

    def capture_lambda_handler(
        self,
        lambda_handler: Any = None,
        capture_response: Optional[bool] = None,
        capture_error: Optional[bool] = None,
    ):
        """Decorator to create subsegment for lambda handlers

        As Lambda follows (event, context) signature we can remove some of the boilerplate
        and also capture any exception any Lambda function throws or its response as metadata

        Parameters
        ----------
        lambda_handler : Callable
            Method to annotate on
        capture_response : bool, optional
            Instructs tracer to not include handler's response as metadata
        capture_error : bool, optional
            Instructs tracer to not include handler's error as metadata, by default True

        Example
        -------
        **Lambda function using capture_lambda_handler decorator**

            tracer = Tracer(service="payment")
            @tracer.capture_lambda_handler
            def handler(event, context):
                ...

        **Preventing Tracer to log response as metadata**

            tracer = Tracer(service="payment")
            @tracer.capture_lambda_handler(capture_response=False)
            def handler(event, context):
                ...

        Raises
        ------
        err
            Exception raised by method
        """
        # If handler is None we've been called with parameters
        # Return a partial function with args filled
        if lambda_handler is None:
            logger.debug("Decorator called with parameters")
            return functools.partial(
                self.capture_lambda_handler,
                capture_response=capture_response,
                capture_error=capture_error,
            )

        lambda_handler_name = lambda_handler.__name__
        capture_response = resolve_truthy_env_var_choice(
            env=os.getenv(constants.TRACER_CAPTURE_RESPONSE_ENV, "true"),
            choice=capture_response,
        )
        capture_error = resolve_truthy_env_var_choice(
            env=os.getenv(constants.TRACER_CAPTURE_ERROR_ENV, "true"),
            choice=capture_error,
        )

        @functools.wraps(lambda_handler)
        def decorate(event, context, **kwargs):
            with self.trace(name=f"## {lambda_handler_name}") as subsegment:
                try:
                    logger.debug("Calling lambda handler")
                    response = lambda_handler(event, context, **kwargs)
                    logger.debug("Received lambda handler response successfully")
                    self._add_response_as_metadata(
                        method_name=lambda_handler_name,
                        data=response,
                        subsegment=subsegment,
                        capture_response=capture_response,
                    )
                except Exception as err:
                    logger.exception(f"Exception received from {lambda_handler_name}")
                    self._add_full_exception_as_metadata(
                        method_name=lambda_handler_name,
                        error=err,
                        subsegment=subsegment,
                        capture_error=capture_error,
                    )

                    raise
                finally:
                    global is_cold_start
                    logger.debug("Annotating cold start")
                    subsegment.put_annotation(key="ColdStart", value=is_cold_start)

                    if is_cold_start:
                        is_cold_start = False

                    if self.service:
                        subsegment.put_annotation(key="Service", value=self.service)

                return response

        return decorate

    # see #465
    @overload
    def capture_method(self, method: "AnyCallableT") -> "AnyCallableT": ...  # pragma: no cover

    @overload
    def capture_method(
        self,
        method: None = None,
        capture_response: Optional[bool] = None,
        capture_error: Optional[bool] = None,
    ) -> Callable[["AnyCallableT"], "AnyCallableT"]: ...  # pragma: no cover

    def capture_method(
        self,
        method: Optional[AnyCallableT] = None,
        capture_response: Optional[bool] = None,
        capture_error: Optional[bool] = None,
    ) -> AnyCallableT:
        """Decorator to create subsegment for arbitrary functions

        It also captures both response and exceptions as metadata
        and creates a subsegment named `## <method_module.method_qualifiedname>`
        # see here: [Qualified name for classes and functions](https://peps.python.org/pep-3155/)

        When running [async functions concurrently](https://docs.python.org/3/library/asyncio-task.html#id6),
        methods may impact each others subsegment, and can trigger
        and AlreadyEndedException from X-Ray due to async nature.

        For this use case, either use `capture_method` only where
        `async.gather` is called, or use `in_subsegment_async`
        context manager via our escape hatch mechanism - See examples.

        Parameters
        ----------
        method : Callable
            Method to annotate on
        capture_response : bool, optional
            Instructs tracer to not include method's response as metadata
        capture_error : bool, optional
            Instructs tracer to not include handler's error as metadata, by default True

        Example
        -------
        **Custom function using capture_method decorator**

            tracer = Tracer(service="payment")
            @tracer.capture_method
            def some_function()

        **Custom async method using capture_method decorator**

            from aws_lambda_powertools import Tracer
            tracer = Tracer(service="booking")

            @tracer.capture_method
            async def confirm_booking(booking_id: str) -> Dict:
                resp = call_to_booking_service()

                tracer.put_annotation("BookingConfirmation", resp["requestId"])
                tracer.put_metadata("Booking confirmation", resp)

                return resp

            def lambda_handler(event: dict, context: Any) -> Dict:
                booking_id = event.get("booking_id")
                asyncio.run(confirm_booking(booking_id=booking_id))

        **Custom generator function using capture_method decorator**

            from aws_lambda_powertools import Tracer
            tracer = Tracer(service="booking")

            @tracer.capture_method
            def bookings_generator(booking_id):
                resp = call_to_booking_service()
                yield resp[0]
                yield resp[1]

            def lambda_handler(event: dict, context: Any) -> Dict:
                gen = bookings_generator(booking_id=booking_id)
                result = list(gen)

        **Custom generator context manager using capture_method decorator**

            from aws_lambda_powertools import Tracer
            tracer = Tracer(service="booking")

            @tracer.capture_method
            @contextlib.contextmanager
            def booking_actions(booking_id):
                resp = call_to_booking_service()
                yield "example result"
                cleanup_stuff()

            def lambda_handler(event: dict, context: Any) -> Dict:
                booking_id = event.get("booking_id")

                with booking_actions(booking_id=booking_id) as booking:
                    result = booking

        **Tracing nested async calls**

            from aws_lambda_powertools import Tracer
            tracer = Tracer(service="booking")

            @tracer.capture_method
            async def get_identity():
                ...

            @tracer.capture_method
            async def long_async_call():
                ...

            @tracer.capture_method
            async def async_tasks():
                await get_identity()
                ret = await long_async_call()

                return { "task": "done", **ret }

        **Safely tracing concurrent async calls with decorator**

        This may not needed once [this bug is closed](https://github.com/aws/aws-xray-sdk-python/issues/164)

            from aws_lambda_powertools import Tracer
            tracer = Tracer(service="booking")

            async def get_identity():
                async with aioboto3.client("sts") as sts:
                    account = await sts.get_caller_identity()
                    return account

            async def long_async_call():
                ...

            @tracer.capture_method
            async def async_tasks():
                _, ret = await asyncio.gather(get_identity(), long_async_call(), return_exceptions=True)

                return { "task": "done", **ret }

        **Safely tracing each concurrent async calls with escape hatch**

        This may not needed once [this bug is closed](https://github.com/aws/aws-xray-sdk-python/issues/164)

            from aws_lambda_powertools import Tracer
            tracer = Tracer(service="booking")

            async def get_identity():
                async tracer.provider.in_subsegment_async("## get_identity"):
                    ...

            async def long_async_call():
                async tracer.provider.in_subsegment_async("## long_async_call"):
                    ...

            @tracer.capture_method
            async def async_tasks():
                _, ret = await asyncio.gather(get_identity(), long_async_call(), return_exceptions=True)

                return { "task": "done", **ret }

        Raises
        ------
        err
            Exception raised by method
        """
        # If method is None we've been called with parameters
        # Return a partial function with args filled
        if method is None:
            logger.debug("Decorator called with parameters")
            return cast(
                AnyCallableT,
                functools.partial(self.capture_method, capture_response=capture_response, capture_error=capture_error),
            )

        # Example: app.ClassA.get_all  # noqa ERA001
        # Valid characters can be found at http://docs.aws.amazon.com/xray/latest/devguide/xray-api-segmentdocuments.html
        method_name = sanitize_xray_segment_name(f"{method.__module__}.{method.__qualname__}")

        capture_response = resolve_truthy_env_var_choice(
            env=os.getenv(constants.TRACER_CAPTURE_RESPONSE_ENV, "true"),
            choice=capture_response,
        )
        capture_error = resolve_truthy_env_var_choice(
            env=os.getenv(constants.TRACER_CAPTURE_ERROR_ENV, "true"),
            choice=capture_error,
        )

        # Maintenance: Need a factory/builder here to simplify this now
        if inspect.iscoroutinefunction(method):
            return self._decorate_async_function(
                method=method,
                capture_response=capture_response,
                capture_error=capture_error,
                method_name=method_name,
            )
        elif inspect.isgeneratorfunction(method):
            return self._decorate_generator_function(
                method=method,
                capture_response=capture_response,
                capture_error=capture_error,
                method_name=method_name,
            )
        elif hasattr(method, "__wrapped__") and inspect.isgeneratorfunction(method.__wrapped__):
            return self._decorate_generator_function_with_context_manager(
                method=method,
                capture_response=capture_response,
                capture_error=capture_error,
                method_name=method_name,
            )
        else:
            return self._decorate_sync_function(
                method=method,
                capture_response=capture_response,
                capture_error=capture_error,
                method_name=method_name,
            )

    def _decorate_async_function(
        self,
        method: Callable,
        capture_response: Optional[Union[bool, str]] = None,
        capture_error: Optional[Union[bool, str]] = None,
        method_name: Optional[str] = None,
    ):
        @functools.wraps(method)
        async def decorate(*args, **kwargs):
            async with self.trace_async(name=f"## {method_name}") as subsegment:
                try:
                    logger.debug(f"Calling method: {method_name}")
                    response = await method(*args, **kwargs)
                    self._add_response_as_metadata(
                        method_name=method_name,
                        data=response,
                        subsegment=subsegment,
                        capture_response=capture_response,
                    )
                except Exception as err:
                    logger.exception(f"Exception received from '{method_name}' method")
                    self._add_full_exception_as_metadata(
                        method_name=method_name,
                        error=err,
                        subsegment=subsegment,
                        capture_error=capture_error,
                    )
                    raise

                return response

        return decorate

    def _decorate_generator_function(
        self,
        method: Callable,
        capture_response: Optional[Union[bool, str]] = None,
        capture_error: Optional[Union[bool, str]] = None,
        method_name: Optional[str] = None,
    ):
        @functools.wraps(method)
        def decorate(*args, **kwargs):
            with self.trace(name=f"## {method_name}") as subsegment:
                try:
                    logger.debug(f"Calling method: {method_name}")
                    result = yield from method(*args, **kwargs)
                    self._add_response_as_metadata(
                        method_name=method_name,
                        data=result,
                        subsegment=subsegment,
                        capture_response=capture_response,
                    )
                except Exception as err:
                    logger.exception(f"Exception received from '{method_name}' method")
                    self._add_full_exception_as_metadata(
                        method_name=method_name,
                        error=err,
                        subsegment=subsegment,
                        capture_error=capture_error,
                    )
                    raise

                return result

        return decorate

    def _decorate_generator_function_with_context_manager(
        self,
        method: Callable,
        capture_response: Optional[Union[bool, str]] = None,
        capture_error: Optional[Union[bool, str]] = None,
        method_name: Optional[str] = None,
    ):
        @functools.wraps(method)
        @contextlib.contextmanager
        def decorate(*args, **kwargs):
            with self.trace(name=f"## {method_name}") as subsegment:
                try:
                    logger.debug(f"Calling method: {method_name}")
                    with method(*args, **kwargs) as return_val:
                        result = return_val
                        yield result
                    self._add_response_as_metadata(
                        method_name=method_name,
                        data=result,
                        subsegment=subsegment,
                        capture_response=capture_response,
                    )
                except Exception as err:
                    logger.exception(f"Exception received from '{method_name}' method")
                    self._add_full_exception_as_metadata(
                        method_name=method_name,
                        error=err,
                        subsegment=subsegment,
                        capture_error=capture_error,
                    )
                    raise

        return decorate

    def _decorate_sync_function(
        self,
        method: AnyCallableT,
        capture_response: Optional[Union[bool, str]] = None,
        capture_error: Optional[Union[bool, str]] = None,
        method_name: Optional[str] = None,
    ) -> AnyCallableT:
        @functools.wraps(method)
        def decorate(*args, **kwargs):
            with self.trace(name=f"## {method_name}") as subsegment:
                try:
                    logger.debug(f"Calling method: {method_name}")
                    response = method(*args, **kwargs)
                    self._add_response_as_metadata(
                        method_name=method_name,
                        data=response,
                        subsegment=subsegment,
                        capture_response=capture_response,
                    )
                except Exception as err:
                    logger.exception(f"Exception received from '{method_name}' method")
                    self._add_full_exception_as_metadata(
                        method_name=method_name,
                        error=err,
                        subsegment=subsegment,
                        capture_error=capture_error,
                    )
                    raise

                return response

        return cast(AnyCallableT, decorate)

    def _add_response_as_metadata(
        self,
        method_name: Optional[str] = None,
        data: Optional[Any] = None,
        subsegment: Optional[BaseSegment] = None,
        capture_response: Optional[Union[bool, str]] = None,
    ):
        """Add response as metadata for given subsegment

        Parameters
        ----------
        method_name : str, optional
            method name to add as metadata key, by default None
        data : Any, optional
            data to add as subsegment metadata, by default None
        subsegment : BaseSegment, optional
            existing subsegment to add metadata on, by default None
        capture_response : bool, optional
            Do not include response as metadata
        """
        if data is None or not capture_response or subsegment is None:
            return

        subsegment.put_metadata(key=f"{method_name} response", value=data, namespace=self.service)

    def _add_full_exception_as_metadata(
        self,
        method_name: str,
        error: Exception,
        subsegment: BaseSegment,
        capture_error: Optional[bool] = None,
    ):
        """Add full exception object as metadata for given subsegment

        Parameters
        ----------
        method_name : str
            method name to add as metadata key, by default None
        error : Exception
            error to add as subsegment metadata, by default None
        subsegment : BaseSegment
            existing subsegment to add metadata on, by default None
        capture_error : bool, optional
            Do not include error as metadata, by default True
        """
        if not capture_error:
            return

        subsegment.put_metadata(key=f"{method_name} error", value=error, namespace=self.service)
