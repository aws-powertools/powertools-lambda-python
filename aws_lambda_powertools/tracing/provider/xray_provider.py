import logging
from contextlib import contextmanager
from typing import Generator, Optional

from ...shared import constants
from ...shared.lazy_import import LazyLoader
from .base import BaseProvider, BaseSegment

logger = logging.getLogger(__name__)
aws_xray_sdk = LazyLoader(constants.XRAY_SDK_MODULE, globals(), constants.XRAY_SDK_MODULE)


class Xray_provider(BaseProvider):
    def __init__(self):
        from aws_xray_sdk.core import xray_recorder  # type: ignore

        self.recorder = xray_recorder
        self.patch = aws_xray_sdk.core.patch
        self.patch_all = aws_xray_sdk.core.patch_all
        self.put_annotation = self.recorder.put_annotation
        self.put_metadata = self.recorder.put_metadata

    @contextmanager
    def trace(self, name=None, **kwargs) -> Generator[BaseSegment, None, None]:
        """Return a subsegment context manger.

        Parameters
        ----------
        name: str
            Subsegment name
        kwargs: Optional[dict]
            Optional parameters to be propagated to segment
        """
        return self.recorder.in_subsegment(name)

    @contextmanager
    def trace_async(self, name=None, **kwargs) -> Generator[BaseSegment, None, None]:
        """Return a subsegment async context manger.

        Parameters
        ----------
        name: str
            Subsegment name
        kwargs: Optional[dict]
            Optional parameters to be propagated to segment
        """
        return self.recorder.in_subsegment_async(name)

    # we don't need to start,end explicitly in xray
    def start_span(self, name=None) -> Generator[BaseSegment, None, None]:
        """This method is proposed as a solution as it exists for other providers
        This method is responsible for starting the trace. This might involve initializing some data structures,
        connecting to an external service, or performing some other setup work"""
        raise Exception("Not implemented")

    def end_span(self, span: BaseSegment):
        """This method is proposed as a solution as it exists for other providers.
        This method is responsible for ending the tracing of a span. This might involve finalizing data structures,
        sending data to an external service, or performing some other cleanup work"""
        raise Exception("Not implemented")

    def put_exception(
        self,
        method_name: str,
        error: Exception,
        subsegment: BaseSegment,
        capture_error: Optional[bool] = None,
        namespace: str = "default",
    ):
        if not capture_error:
            return
        self.put_metadata(key=f"{method_name} error", value=error, namespace=namespace)
