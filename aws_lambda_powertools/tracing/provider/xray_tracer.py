from __future__ import annotations

from contextlib import contextmanager
from numbers import Number
from typing import Generator

from ...shared import constants
from ...shared.lazy_import import LazyLoader
from .base import BaseProvider, BaseSpan

aws_xray_sdk = LazyLoader(constants.XRAY_SDK_MODULE, globals(), constants.XRAY_SDK_MODULE)


class XraySpan(BaseSpan):
    def __init__(self, subsegment):
        self.subsegment = subsegment
        self.add_subsegment = self.subsegment.add_subsegment
        self.remove_subsegment = self.subsegment.remove_subsegment
        self.put_annotation = self.subsegment.put_annotation
        self.put_metadata = self.subsegment.put_metadata
        self.add_exception = self.subsegment.add_exception
        self.close = self.subsegment.close

    def set_attribute(self, key: str, value: str | Number | bool, **kwargs) -> None:
        if kwargs.get("namespace", "") != "":
            self.put_metadata(key=key, value=value, namespace=kwargs["namespace"])
        else:
            self.put_annotation(key=key, value=value)

    def record_exception(self, exception: BaseException, **kwargs):
        stack = aws_xray_sdk.core.utils.stacktrace.get_stacktrace(limit=self._max_trace_back)
        self.add_exception(exception=exception, stack=stack)


class XrayProvider(BaseProvider):
    def __init__(self, xray_recorder=None):
        if not xray_recorder:
            from aws_xray_sdk.core import xray_recorder
        self.recorder = xray_recorder
        self.patch = aws_xray_sdk.core.patch
        self.patch_all = aws_xray_sdk.core.patch_all
        self.in_subsegment = self.recorder.in_subsegment
        self.in_subsegment_async = self.recorder.in_subsegment_async
        self.put_annotation = self.recorder.put_annotation
        self.put_metadata = self.recorder.put_metadata

    @contextmanager
    def trace(self, name: str) -> Generator[XraySpan, None, None]:
        with self.in_subsegment(name=name) as sub_segment:
            yield XraySpan(subsegment=sub_segment)

    @contextmanager
    def trace_async(self, name: str) -> Generator[XraySpan, None, None]:
        with self.in_subsegment_async(name=name) as sub_segment:
            yield XraySpan(subsegment=sub_segment)

    def set_attribute(self, key: str, value: str | Number | bool, **kwargs) -> None:
        if kwargs.get("namespace", "") != "":
            self.put_metadata(key=key, value=value, namespace=kwargs["namespace"])
        else:
            self.put_annotation(key=key, value=value)
