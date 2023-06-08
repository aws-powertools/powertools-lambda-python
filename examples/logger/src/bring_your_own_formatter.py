from __future__ import annotations

from typing import Mapping

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter
from aws_lambda_powertools.logging.types import PowertoolsLogRecord


class CustomFormatter(LambdaPowertoolsFormatter):
    def serialize(self, log: PowertoolsLogRecord | Mapping) -> str:  
        """Serialize final structured log dict to JSON str"""
        log["event"] = log.pop("message")  # type: ignore
        return self.json_serializer(log)  


logger = Logger(service="payment", logger_formatter=CustomFormatter())
logger.info("hello")
