from __future__ import annotations

import logging
from numbers import Number
from traceback import StackSummary
from typing import Any, Generator, List, Optional, Sequence

import ddtrace

from ..base import BaseProvider, BaseSegment

logger = logging.getLogger(__name__)


class DDSpan(BaseSegment):
    def __init__(self, dd_span=ddtrace.Span):
        self.dd_span = dd_span

    def close(self, end_time: int | None = None):
        print("close is called")
        if end_time:
            end_time = float(end_time)
        self.dd_span.finish(finish_time=end_time)

    def add_subsegment(self, subsegment: Any):
        raise NotImplementedError

    def remove_subsegment(self, subsegment: Any):
        raise NotImplementedError

    def put_annotation(self, key: str, value: str | Number | bool) -> None:
        self.dd_span.set_tag(key=key, value=value)

    def put_metadata(self, key: str, value: Any, namespace: str = "default") -> None:
        self.dd_span.set_tag(key=f"{namespace}.{key}", value=value)

    def add_exception(self, exception: BaseException, stack: List[StackSummary], remote: bool = False):
        self.dd_span.set_exc_info(exc_type=exception, exc_val=exception, exc_tb=stack)

    def __enter__(self):
        print("entered")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                self.dd_span.set_exc_info(exc_type, exc_val, exc_tb)
            print("exited")
            self.close()
        except Exception as e:
            logger.exception(f"error closing trace {e}")


class DDTraceProvider(BaseProvider):
    def __init__(self, dd_tracer: ddtrace.Tracer):
        self.dd_tracer = dd_tracer

    def in_subsegment(
        self,
        name=None,
        service: Optional[str] = None,
        resource: Optional[str] = None,
        span_type: Optional[str] = None,
        **kwargs,
    ) -> Generator[BaseSegment, None, None]:
        dd_span = self.dd_tracer.trace(
            name,
            service=service,
            resource=resource,
            span_type=span_type,
        )
        return DDSpan(dd_span=dd_span)

    in_subsegment_async = in_subsegment

    def put_annotation(self, key: str, value: str | Number | bool) -> None:
        self.dd_tracer.context_provider.active().set_tag(key=key, value=value)

    def put_metadata(self, key: str, value: Any, namespace: str = "default") -> None:
        self.dd_tracer.context_provider.active().set_tag(key=f"{namespace}.{key}", value=value)

    def patch(self, modules: Sequence[str]) -> None:
        module_to_patch = {}
        for m in modules:
            module_to_patch[m] = True
        ddtrace.patch(**module_to_patch)

    def patch_all(self) -> None:
        ddtrace.patch_all()
