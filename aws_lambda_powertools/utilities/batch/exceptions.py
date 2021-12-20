"""
Batch processing exceptions
"""
import traceback
from types import TracebackType
from typing import List, Optional, Tuple, Type

ExceptionInfo = Tuple[Type[BaseException], BaseException, TracebackType]


class BaseBatchProcessingError(Exception):
    def __init__(self, msg="", child_exceptions: Optional[List[ExceptionInfo]] = None):
        super().__init__(msg)
        self.msg = msg
        self.child_exceptions = child_exceptions

    def format_exceptions(self, parent_exception_str):
        exception_list = [f"{parent_exception_str}\n"]
        for exception in self.child_exceptions:
            extype, ex, tb = exception
            formatted = "".join(traceback.format_exception(extype, ex, tb))
            exception_list.append(formatted)

        return "\n".join(exception_list)


class SQSBatchProcessingError(BaseBatchProcessingError):
    """When at least one message within a batch could not be processed"""

    def __init__(self, msg="", child_exceptions: Optional[List[ExceptionInfo]] = None):
        super().__init__(msg, child_exceptions)

    # Overriding this method so we can output all child exception tracebacks when we raise this exception to prevent
    # errors being lost. See https://github.com/awslabs/aws-lambda-powertools-python/issues/275
    def __str__(self):
        parent_exception_str = super(SQSBatchProcessingError, self).__str__()
        return self.format_exceptions(parent_exception_str)


class BatchProcessingError(BaseBatchProcessingError):
    """When all batch records failed to be processed"""

    def __init__(self, msg="", child_exceptions: Optional[List[ExceptionInfo]] = None):
        super().__init__(msg, child_exceptions)

    def __str__(self):
        parent_exception_str = super(BatchProcessingError, self).__str__()
        return self.format_exceptions(parent_exception_str)
