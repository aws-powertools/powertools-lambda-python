from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter
from aws_lambda_powertools.logging.types import TypedLog


class CustomFormatter(LambdaPowertoolsFormatter):
    def serialize(self, log: TypedLog) -> str:  # type: ignore
        """Serialize final structured log dict to JSON str"""
        log["event"] = log.pop("message")  # type: ignore
        return self.json_serializer(log)  # type: ignore


logger = Logger(service="payment", logger_formatter=CustomFormatter())
logger.info("hello")
