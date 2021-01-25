"""
Batch processing exceptions
"""
import traceback


class SQSBatchProcessingError(Exception):
    """When at least one message within a batch could not be processed"""

    def __init__(self, msg="", child_exceptions=()):
        super().__init__(msg)
        self.msg = msg
        self.child_exceptions = child_exceptions

    def __str__(self):
        parent_exception_str = super(SQSBatchProcessingError, self).__str__()
        exception_list = [f"{parent_exception_str}\n"]
        for exception in self.child_exceptions:
            extype, ex, tb = exception
            formatted = "".join(traceback.format_exception(extype, ex, tb))
            exception_list.append(formatted)

        return "\n".join(exception_list)
