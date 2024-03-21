from __future__ import annotations

import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Dict, Generator, Optional, Sequence

from opentelemetry import trace as otel_trace

from ..base import BaseProvider, BaseSpan

logger = logging.getLogger(__name__)


# optl terminology first
# 1. Provider based on OTel terminology
# 2. X-Ray provider on top of the new BaseProvider
# 3. Datadog provider on top of the new BaseProvider
# access xray sdk
class OtelSpan(BaseSpan):
    def __init__(self, otel_span=otel_trace.Span):
        self.otel_span = otel_span

    def set_attribute(self, key: str, value: str | float | bool, **kwargs) -> None:  # type: ignore[override]
        self.otel_span.set_attribute(key=key, value=value)

    def record_exception(
        self,
        exception: BaseException,
        attributes: Optional[Dict] = None,
        timestamp: Optional[int] = None,
        escaped: bool = False,
        **kwargs,
    ):
        _attributes = attributes or {}
        if kwargs:
            kwargs.update(_attributes)
            # attribute should overwrite kwargs
            _attributes = kwargs
        self.otel_span.record_exception(
            exception=exception,
            attributes=_attributes,
            timestamp=timestamp,
            escaped=escaped,
        )

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
    def trace(self, name: str, **kwargs) -> Generator[OtelSpan, None, None]:
        with self.otel_tracer.start_as_current_span(name=name, **kwargs) as otel_span:
            yield OtelSpan(otel_span=otel_span)

    in_subsegment = trace

    @asynccontextmanager
    async def trace_async(self, name: str, **kwargs) -> AsyncGenerator[OtelSpan, None]:
        with self.otel_tracer.start_as_current_span(name=name, **kwargs) as otel_span:
            yield OtelSpan(otel_span=otel_span)

    in_subsegment_async = trace_async

    def set_attribute(self, key: str, value: str | float | bool, **kwargs) -> None:  # type: ignore[override]
        active_span = otel_trace.get_current_span()
        active_span.set_attribute(key=key, value=value)

    def patch(self, modules: Sequence[str]) -> None:
        # OTEL sdk doesn't have patch
        pass

    def patch_all(self) -> None:
        # OTEL sdk doesn't have patch
        pass
