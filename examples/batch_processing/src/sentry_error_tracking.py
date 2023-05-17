from sentry_sdk import capture_exception

from aws_lambda_powertools.utilities.batch import BatchProcessor, FailureResponse


class MyProcessor(BatchProcessor):
    def failure_handler(self, record, exception) -> FailureResponse:
        capture_exception()  # send exception to Sentry
        return super().failure_handler(record, exception)
