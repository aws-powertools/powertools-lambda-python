from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter
from aws_lambda_powertools.logging.types import LogRecord


class CustomFormatter(LambdaPowertoolsFormatter):
    def serialize(self, log: LogRecord) -> str:
        """Serialize final structured log dict to JSON str"""
        # in this example, log["message"] is a required field
        # but we want to remap to "event" and delete "message", hence mypy ignore checks
        log["event"] = log.pop("message")  # type: ignore[typeddict-unknown-key,misc]
        return self.json_serializer(log)


logger = Logger(service="payment", logger_formatter=CustomFormatter())
logger.info("hello")
