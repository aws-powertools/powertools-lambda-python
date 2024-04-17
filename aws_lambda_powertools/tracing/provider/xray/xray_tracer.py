from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from numbers import Number
from typing import Any, AsyncGenerator, Generator, Literal, Sequence, Union

from ....shared import constants
from ....shared.lazy_import import LazyLoader
from ..base import BaseProvider, BaseSpan

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

    def set_attribute(
        self,
        key: str,
        value: Any,
        category: Literal["Annotation", "Metadata", "Auto"] = "Auto",
        **kwargs,
    ) -> None:
        """
        Set an attribute on this span with a key-value pair.

        Parameters
        ----------
        key: str
            attribute key
        value: Any
            Value for attribute
        category: Literal["Annotation","Metadata","Auto"] = "Auto"
            This parameter specifies the category of attribute to set.
            - **"Annotation"**: Sets the attribute as an Annotation.
            - **"Metadata"**: Sets the attribute as Metadata.
            - **"Auto" (default)**: Automatically determines the attribute
            type based on its value.

        kwargs: Optional[dict]
            Optional parameters to be passed to provider.set_attributes
        """
        if category == "Annotation":
            self.put_annotation(key=key, value=value)
            return

        if category == "Metadata":
            self.put_metadata(key=key, value=value, namespace=kwargs.get("namespace", "dafault"))
            return

        # Auto
        if isinstance(value, (str, Number, bool)):
            self.put_annotation(key=key, value=value)
            return

        # Auto & not in (str, Number, bool)
        self.put_metadata(key=key, value=value, namespace=kwargs.get("namespace", "dafault"))

    def record_exception(self, exception: BaseException, **kwargs):
        stack = aws_xray_sdk.core.utils.stacktrace.get_stacktrace()
        self.add_exception(exception=exception, stack=stack)


class XrayProvider(BaseProvider):
    def __init__(self, xray_recorder=None):
        if not xray_recorder:
            from aws_xray_sdk.core import xray_recorder
        self.recorder = xray_recorder
        self.in_subsegment = self.recorder.in_subsegment
        self.in_subsegment_async = self.recorder.in_subsegment_async

    @contextmanager
    def trace(self, name: str, **kwargs) -> Generator[XraySpan, None, None]:
        with self.in_subsegment(name=name, **kwargs) as sub_segment:
            yield XraySpan(subsegment=sub_segment)

    @asynccontextmanager
    async def trace_async(self, name: str, **kwargs) -> AsyncGenerator[XraySpan, None]:
        async with self.in_subsegment_async(name=name, **kwargs) as subsegment:
            yield XraySpan(subsegment=subsegment)

    def set_attribute(
        self,
        key: str,
        value: Any,
        category: Literal["Annotation", "Metadata", "Auto"] = "Auto",
        **kwargs,
    ) -> None:
        """
        Set an attribute on the current active span with a key-value pair.

        Parameters
        ----------
        key: str
            attribute key
        value: Any
            Value for attribute
        category: Literal["Annotation","Metadata","Auto"] = "Auto"
            This parameter specifies the type of attribute to set.
            - **"Annotation"**: Sets the attribute as an Annotation.
            - **"Metadata"**: Sets the attribute as Metadata.
            - **"Auto" (default)**: Automatically determines the attribute
            type based on its value.

        kwargs: Optional[dict]
            Optional parameters to be passed to provider.set_attributes
        """
        if category == "Annotation":
            self.put_annotation(key=key, value=value)
            return

        if category == "Metadata":
            self.put_metadata(key=key, value=value, namespace=kwargs.get("namespace", "dafault"))
            return

        # Auto
        if isinstance(value, (str, Number, bool)):
            self.put_annotation(key=key, value=value)
            return

        # Auto & not in (str, Number, bool)
        self.put_metadata(key=key, value=value, namespace=kwargs.get("namespace", "dafault"))

    def put_annotation(self, key: str, value: Union[str, Number, bool]) -> None:
        return self.recorder.put_annotation(key=key, value=value)

    def put_metadata(self, key: str, value: Any, namespace: str = "default") -> None:
        return self.recorder.put_metadata(key=key, value=value, namespace=namespace)

    def patch(self, modules: Sequence[str]) -> None:
        return aws_xray_sdk.core.patch(modules)

    def patch_all(self) -> None:
        return aws_xray_sdk.core.patch_all()
