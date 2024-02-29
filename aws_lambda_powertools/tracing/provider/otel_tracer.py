from __future__ import annotations

import logging
from contextlib import contextmanager
from numbers import Number
from traceback import StackSummary
from typing import Any, Generator, List, Sequence

from opentelemetry import trace as otel_trace

from ..base import BaseProvider, BaseSegment

logger = logging.getLogger(__name__)


# optl terminology first
# 1. Provider based on OTel terminology
# 2. X-Ray provider on top of the new BaseProvider
# 3. Datadog provider on top of the new BaseProvider
# access xray sdk
class OtelSpan(BaseSegment):
    def __init__(self, otel_span=otel_trace.Span):
        self.otel_span = otel_span

    def close(self, end_time: int | None = None):
        print("close is called")
        self.otel_span.end(end_time=end_time)

    def add_subsegment(self, subsegment: Any):
        raise NotImplementedError

    def remove_subsegment(self, subsegment: Any):
        raise NotImplementedError

    def put_annotation(self, key: str, value: str | Number | bool) -> None:
        self.otel_span.set_attribute(key=key, value=value)

    def put_metadata(self, key: str, value: Any, namespace: str = "default") -> None:
        self.otel_span.set_attribute(key=f"{namespace}.{key}", value=str(value))

    def add_exception(self, exception: BaseException, stack: List[StackSummary], remote: bool = False):
        self.otel_span.record_exception(exception=exception, attributes={"traceback": stack, "remote": remote})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.otel_span.__exit__(exc_type, exc_val, exc_tb)
        except Exception as e:
            logger.exception(f"error closing trace {e}")


class OtelProvider(BaseProvider):
    def __init__(self, otel_tracer: otel_trace.Tracer):
        self.otel_tracer = otel_tracer

    @contextmanager
    def in_subsegment(self, name: str, **kwargs) -> Generator[BaseSegment, None, None]:
        with self.otel_tracer.start_as_current_span(name=name, **kwargs) as otel_span:
            yield OtelSpan(otel_span=otel_span)

    start_as_current_span = in_subsegment
    in_subsegment_async = in_subsegment

    def put_annotation(self, key: str, value: str | Number | bool) -> None:
        active_span = otel_trace.get_current_span()
        active_span.set_attribute(key=key, value=value)

    def put_metadata(self, key: str, value: Any, namespace: str = "default") -> None:
        active_span = otel_trace.get_current_span()
        active_span.set_attribute(key=f"{namespace}.{key}", value=value)

    def patch(self, modules: Sequence[str]) -> None:
        # OTEL sdk doesn't have patch
        pass

    def patch_all(self) -> None:
        pass
