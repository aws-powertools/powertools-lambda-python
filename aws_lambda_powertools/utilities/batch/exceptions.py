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

    # Overriding this method so we can output all child exception tracebacks when we raise this exception to prevent
    # errors being lost. See https://github.com/awslabs/aws-lambda-powertools-python/issues/275
    def __str__(self):
        parent_exception_str = super(SQSBatchProcessingError, self).__str__()
        exception_list = [f"{parent_exception_str}\n"]
        for exception in self.child_exceptions:
            extype, ex, tb = exception
            formatted = "".join(traceback.format_exception(extype, ex, tb))
            exception_list.append(formatted)

        return "\n".join(exception_list)
