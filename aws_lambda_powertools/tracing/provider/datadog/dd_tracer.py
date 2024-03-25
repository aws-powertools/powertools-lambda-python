from __future__ import annotations

import logging
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Dict, Generator, Optional, Sequence

import ddtrace

from ..base import BaseProvider, BaseSpan

logger = logging.getLogger(__name__)


class DDSpan(BaseSpan):
    def __init__(self, dd_span=ddtrace.Span):
        self.dd_span = dd_span

    def set_attribute(self, key: str | bytes, value: Any, **kwargs) -> None:
        self.dd_span.set_tag(key=key, value=value)

    def record_exception(self, exception: BaseException, attributes: Optional[Dict] = None, **kwargs):
        self.dd_span.set_traceback()
        _attributes = attributes or {}
        if kwargs:
            kwargs.update(_attributes)
            # attribute should overwrite kwargs
            _attributes = kwargs
        self.dd_span.set_tags(tags=attributes)


class DDTraceProvider(BaseProvider):
    def __init__(self, dd_tracer: ddtrace.Tracer):
        self.dd_tracer = dd_tracer

    @contextmanager
    def trace(
        self,
        name: str,
        service: Optional[str] = None,
        resource: Optional[str] = None,
        span_type: Optional[str] = None,
        **kwargs,
    ) -> Generator[DDSpan, None, None]:
        with self.dd_tracer.trace(
            name=name,
            service=service,
            resource=resource,
            span_type=span_type,
        ) as dd_span:
            yield DDSpan(dd_span=dd_span)

    in_subsegment = trace

    @asynccontextmanager
    async def trace_async(
        self,
        name: str,
        service: Optional[str] = None,
        resource: Optional[str] = None,
        span_type: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[DDSpan, None]:
        with self.dd_tracer.trace(
            name=name,
            service=service,
            resource=resource,
            span_type=span_type,
        ) as dd_span:
            yield DDSpan(dd_span=dd_span)

    def set_attribute(self, key: str | bytes, value: Any, **kwargs: Any) -> None:
        span = self.dd_tracer.context_provider.active()
        # ignore if no active span
        if isinstance(span, ddtrace.Span):
            span.set_tag(key=key, value=value)

    def patch(self, modules: Sequence[str]) -> None:
        module_to_patch = {}
        for m in modules:
            module_to_patch[m] = True
        ddtrace.patch(**module_to_patch)  # type:ignore

    def patch_all(self) -> None:
        ddtrace.patch_all()
