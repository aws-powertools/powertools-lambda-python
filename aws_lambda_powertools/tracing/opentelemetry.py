from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator, Sequence

from aws_lambda_powertools.tracing.base import BaseProvider, BaseSegment

if TYPE_CHECKING:
    import numbers
    import traceback


class OpenTelemetrySegment(BaseSegment):
    """Segment implementation wrapping an OpenTelemetry Span."""

    def __init__(self, span: Any):
        self.span = span

    def close(self, end_time: int | None = None):
        if self.span and hasattr(self.span, "end"):
            if end_time is not None:
                self.span.end(end_time=int(end_time * 1e9))
            else:
                self.span.end()

    def add_subsegment(self, subsegment: Any):
        pass

    def remove_subsegment(self, subsegment: Any):
        pass

    def put_annotation(self, key: str, value: str | numbers.Number | bool) -> None:
        if self.span and hasattr(self.span, "set_attribute"):
            self.span.set_attribute(key, value)

    def put_metadata(self, key: str, value: Any, namespace: str = "default") -> None:
        if self.span and hasattr(self.span, "set_attribute"):
            attr_key = f"{namespace}.{key}" if namespace else key
            self.span.set_attribute(attr_key, str(value))

    def add_exception(
        self,
        exception: BaseException,
        stack: list[traceback.StackSummary] | None = None,
        remote: bool = False,
    ):
        if self.span and hasattr(self.span, "record_exception"):
            self.span.record_exception(exception)


class OpenTelemetryProvider(BaseProvider):
    """Tracing provider utilizing OpenTelemetry for Powertools Tracer."""

    def __init__(self, tracer: Any | None = None):
        if tracer is None:
            try:
                from opentelemetry import trace

                tracer = trace.get_tracer("aws_lambda_powertools")
            except ImportError:
                tracer = None
        self._tracer = tracer

    @contextmanager
    def in_subsegment(self, name: str | None = None, **kwargs) -> Generator[BaseSegment, None, None]:
        name = name or "subsegment"
        if self._tracer is not None:
            with self._tracer.start_as_current_span(name) as span:
                yield OpenTelemetrySegment(span)
        else:
            yield OpenTelemetrySegment(None)

    @contextmanager
    def in_subsegment_async(self, name: str | None = None, **kwargs) -> Generator[BaseSegment, None, None]:
        name = name or "subsegment"
        if self._tracer is not None:
            with self._tracer.start_as_current_span(name) as span:
                yield OpenTelemetrySegment(span)
        else:
            yield OpenTelemetrySegment(None)

    def put_annotation(self, key: str, value: str | numbers.Number | bool) -> None:
        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            if span and hasattr(span, "set_attribute"):
                span.set_attribute(key, value)
        except ImportError:
            pass

    def put_metadata(self, key: str, value: Any, namespace: str = "default") -> None:
        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            if span and hasattr(span, "set_attribute"):
                attr_key = f"{namespace}.{key}" if namespace else key
                span.set_attribute(attr_key, str(value))
        except ImportError:
            pass

    def patch(self, modules: Sequence[str]) -> None:
        pass

    def patch_all(self) -> None:
        pass
