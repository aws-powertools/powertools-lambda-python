"""
Batch processing exceptions
"""

from __future__ import annotations

import traceback
from types import TracebackType
from typing import Optional, Tuple, Type

ExceptionInfo = Tuple[Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]]


class BaseBatchProcessingError(Exception):
    def __init__(self, msg="", child_exceptions: list[ExceptionInfo] | None = None):
        super().__init__(msg)
        self.msg = msg
        self.child_exceptions = child_exceptions or []

    def format_exceptions(self, parent_exception_str):
        exception_list = [f"{parent_exception_str}\n"]
        for exception in self.child_exceptions:
            extype, ex, tb = exception
            formatted = "".join(traceback.format_exception(extype, ex, tb))
            exception_list.append(formatted)

        return "\n".join(exception_list)


class BatchProcessingError(BaseBatchProcessingError):
    """When all batch records failed to be processed"""

    def __init__(self, msg="", child_exceptions: list[ExceptionInfo] | None = None):
        super().__init__(msg, child_exceptions)

    def __str__(self):
        parent_exception_str = super().__str__()
        return self.format_exceptions(parent_exception_str)


class SQSFifoCircuitBreakerError(Exception):
    """
    Signals a record not processed due to the SQS FIFO processing being interrupted
    """

    pass


class SQSFifoMessageGroupCircuitBreakerError(Exception):
    """
    Signals a record not processed due to the SQS FIFO message group processing being interrupted
    """

    pass
