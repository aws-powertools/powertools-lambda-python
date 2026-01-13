"""OpenTelemetry Tracer implementation for AWS Lambda Powertools"""

from __future__ import annotations

import contextlib
import functools
import inspect
import logging
import os
from typing import TYPE_CHECKING, Literal, TypeVar

from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import resolve_env_var_choice, resolve_truthy_env_var_choice

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from opentelemetry.sdk.trace import TracerProvider as SDKTracerProvider
    from opentelemetry.trace import Span, Tracer, TracerProvider

logger = logging.getLogger(__name__)

is_cold_start = True
T = TypeVar("T")


def _is_cold_start() -> bool:
    """Check if this is a cold start invocation."""
    global is_cold_start

    if os.getenv(constants.LAMBDA_INITIALIZATION_TYPE) == "provisioned-concurrency":
        is_cold_start = False
        return False

    if not is_cold_start:
        return False

    is_cold_start = False
    return True


class TracerOpenTelemetry:
    """OpenTelemetry Tracer for AWS Lambda with Powertools conventions.

    Parameters
    ----------
    mode : Literal["auto", "manual"]
        Instrumentation mode. "auto" uses global TracerProvider from OTel SDK (e.g., ADOT).
        "manual" uses provided TracerProvider or creates default one.
    service : str, optional
        Service name for spans. Falls back to POWERTOOLS_SERVICE_NAME or Lambda function name.
    tracer_provider : TracerProvider, optional
        Custom TracerProvider. Only valid in manual mode.
    disabled : bool, optional
        Disable tracing. Falls back to POWERTOOLS_TRACE_DISABLED env var.

    Example
    -------
    **Auto mode with ADOT Lambda Layer:**

        from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

        tracer = TracerOpenTelemetry(mode="auto")

        @tracer.capture_lambda_handler
        def handler(event, context):
            return {"statusCode": 200}

    **Manual mode with custom TracerProvider:**

        from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))

        tracer = TracerOpenTelemetry(mode="manual", tracer_provider=provider)
    """

    def __init__(
        self,
        mode: Literal["auto", "manual"] = "manual",
        service: str | None = None,
        tracer_provider: SDKTracerProvider | None = None,
        disabled: bool | None = None,
    ):
        self.mode = mode
        self.disabled = self._resolve_disabled(disabled)
        self.service = self._resolve_service(service)
        self._tracer_provider = self._resolve_tracer_provider(tracer_provider)
        self._tracer: Tracer | None = None

    def _resolve_disabled(self, disabled: bool | None) -> bool:
        """Resolve disabled state from parameter or environment."""
        if disabled is not None:
            return disabled
        return resolve_truthy_env_var_choice(env=os.getenv(constants.TRACER_DISABLED_ENV, "false"))

    def _resolve_service(self, service: str | None) -> str:
        """Resolve service name from parameter, environment, or Lambda context."""
        if service:
            return service
        return resolve_env_var_choice(
            choice=service,
            env=os.getenv(constants.SERVICE_NAME_ENV) or os.getenv("AWS_LAMBDA_FUNCTION_NAME", "service_undefined"),
        )

    def _resolve_tracer_provider(self, tracer_provider: SDKTracerProvider | None) -> SDKTracerProvider | None:
        """Resolve TracerProvider based on mode."""
        if self.disabled:
            return None

        if self.mode == "auto":
            if tracer_provider is not None:
                raise ValueError("tracer_provider cannot be provided in auto mode")
            return None  # Will use global provider

        # Manual mode: use provided or create default
        if tracer_provider is not None:
            return tracer_provider

        # Create default TracerProvider
        from opentelemetry.sdk.trace import TracerProvider as SDKTracerProvider

        return SDKTracerProvider()

    @property
    def provider(self) -> TracerProvider:
        """Get the TracerProvider."""
        if self._tracer_provider is not None:
            return self._tracer_provider

        from opentelemetry.trace import get_tracer_provider

        return get_tracer_provider()  # type: ignore[return-value]

    def _get_tracer(self) -> Tracer:
        """Get or create the Tracer instance."""
        if self._tracer is None:
            self._tracer = self.provider.get_tracer(
                instrumenting_module_name="aws_lambda_powertools",
                instrumenting_library_version="1.0.0",
            )
        return self._tracer

    def capture_lambda_handler(
        self,
        lambda_handler: Callable | None = None,
        capture_response: bool | None = None,
        capture_error: bool | None = None,
    ) -> Callable:
        """Decorator to trace Lambda handler with cold start detection.

        Parameters
        ----------
        capture_response : bool, optional
            Capture response as span attribute. Default True.
        capture_error : bool, optional
            Capture errors as span events. Default True.
        """
        if lambda_handler is None:
            return functools.partial(
                self.capture_lambda_handler,
                capture_response=capture_response,
                capture_error=capture_error,
            )

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
            if self.disabled:
                return lambda_handler(event, context, **kwargs)

            tracer = self._get_tracer()
            with tracer.start_as_current_span(
                name=lambda_handler.__name__,
                record_exception=capture_error,
                set_status_on_exception=True,
            ) as span:
                self._add_lambda_attributes(span)

                try:
                    response = lambda_handler(event, context, **kwargs)
                    if capture_response and response is not None:
                        span.set_attribute(f"{lambda_handler.__name__}.response", str(response)[:1024])
                    return response
                except Exception as err:
                    if capture_error:
                        span.record_exception(err)
                    raise

        return decorate

    def _add_lambda_attributes(self, span: Span) -> None:
        """Add Lambda-specific attributes to span."""
        cold_start = _is_cold_start()
        span.set_attribute("faas.coldstart", cold_start)
        span.set_attribute("service.name", self.service)

    def capture_method(
        self,
        method: Callable | None = None,
        capture_response: bool | None = None,
        capture_error: bool | None = None,
    ) -> Callable:
        """Decorator to trace methods as child spans.

        Parameters
        ----------
        capture_response : bool, optional
            Capture response as span attribute. Default True.
        capture_error : bool, optional
            Capture errors as span events. Default True.
        """
        if method is None:
            return functools.partial(
                self.capture_method,
                capture_response=capture_response,
                capture_error=capture_error,
            )

        method_name = f"{method.__module__}.{method.__qualname__}"

        capture_response = resolve_truthy_env_var_choice(
            env=os.getenv(constants.TRACER_CAPTURE_RESPONSE_ENV, "true"),
            choice=capture_response,
        )
        capture_error = resolve_truthy_env_var_choice(
            env=os.getenv(constants.TRACER_CAPTURE_ERROR_ENV, "true"),
            choice=capture_error,
        )

        if inspect.iscoroutinefunction(method):
            return self._decorate_async(method, method_name, capture_response, capture_error)
        elif inspect.isgeneratorfunction(method):
            return self._decorate_generator(method, method_name, capture_response, capture_error)
        else:
            return self._decorate_sync(method, method_name, capture_response, capture_error)

    def _decorate_sync(
        self,
        method: Callable,
        method_name: str,
        capture_response: bool,
        capture_error: bool,
    ) -> Callable:
        @functools.wraps(method)
        def decorate(*args, **kwargs):
            if self.disabled:
                return method(*args, **kwargs)

            tracer = self._get_tracer()
            with tracer.start_as_current_span(
                name=method_name,
                record_exception=capture_error,
                set_status_on_exception=True,
            ) as span:
                try:
                    response = method(*args, **kwargs)
                    if capture_response and response is not None:
                        span.set_attribute(f"{method_name}.response", str(response)[:1024])
                    return response
                except Exception as err:
                    if capture_error:
                        span.record_exception(err)
                    raise

        return decorate

    def _decorate_async(
        self,
        method: Callable,
        method_name: str,
        capture_response: bool,
        capture_error: bool,
    ) -> Callable:
        @functools.wraps(method)
        async def decorate(*args, **kwargs):
            if self.disabled:
                return await method(*args, **kwargs)

            tracer = self._get_tracer()
            with tracer.start_as_current_span(
                name=method_name,
                record_exception=capture_error,
                set_status_on_exception=True,
            ) as span:
                try:
                    response = await method(*args, **kwargs)
                    if capture_response and response is not None:
                        span.set_attribute(f"{method_name}.response", str(response)[:1024])
                    return response
                except Exception as err:
                    if capture_error:
                        span.record_exception(err)
                    raise

        return decorate

    def _decorate_generator(
        self,
        method: Callable,
        method_name: str,
        capture_response: bool,
        capture_error: bool,
    ) -> Callable:
        @functools.wraps(method)
        def decorate(*args, **kwargs):
            if self.disabled:
                yield from method(*args, **kwargs)
                return

            tracer = self._get_tracer()
            with tracer.start_as_current_span(
                name=method_name,
                record_exception=capture_error,
                set_status_on_exception=True,
            ) as span:
                try:
                    response = yield from method(*args, **kwargs)
                    if capture_response and response is not None:
                        span.set_attribute(f"{method_name}.response", str(response)[:1024])
                    return response
                except Exception as err:
                    if capture_error:
                        span.record_exception(err)
                    raise

        return decorate

    @contextlib.contextmanager
    def add_span(
        self,
        name: str,
        **kwargs,
    ) -> Generator[Span, None, None]:
        """Context manager to create a child span.

        Parameters
        ----------
        name : str
            Span name.
        **kwargs
            Additional arguments passed to start_as_current_span.

        Example
        -------
            with tracer.add_span("process_data") as span:
                span.set_attribute("items", 10)
                process()
        """
        if self.disabled:
            yield None  # type: ignore[misc]
            return

        tracer = self._get_tracer()
        kwargs.setdefault("record_exception", True)
        kwargs.setdefault("set_status_on_exception", True)

        with tracer.start_as_current_span(name=name, **kwargs) as span:
            yield span

    def get_current_span(self) -> Span | None:
        """Get the current active span.

        Returns
        -------
        Span | None
            Current span or None if no active span.
        """
        if self.disabled:
            return None

        from opentelemetry.trace import get_current_span

        return get_current_span()

    def instrument_requests(self, ignore_urls: list[str] | None = None) -> None:
        """Configure requests library instrumentation with URL filtering.

        Parameters
        ----------
        ignore_urls : list[str], optional
            List of URL patterns to exclude from tracing.

        Note
        ----
        Requires opentelemetry-instrumentation-requests package.
        """
        if self.disabled:
            return

        try:
            from opentelemetry.instrumentation.requests import RequestsInstrumentor  # type: ignore[import-not-found]

            if ignore_urls:
                os.environ["OTEL_PYTHON_REQUESTS_EXCLUDED_URLS"] = ",".join(ignore_urls)

            RequestsInstrumentor().instrument()
        except ImportError:
            logger.warning("opentelemetry-instrumentation-requests not installed, skipping instrumentation")
