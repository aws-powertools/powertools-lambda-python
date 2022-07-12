from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter


class CustomFormatter(LambdaPowertoolsFormatter):
    def serialize(self, log: dict) -> str:
        """Serialize final structured log dict to JSON str"""
        log["event"] = log.pop("message")  # rename message key to event
        return self.json_serializer(log)  # use configured json serializer


logger = Logger(service="payment", logger_formatter=CustomFormatter())
logger.info("hello")
