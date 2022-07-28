import json
import logging
from typing import Iterable, List, Optional

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.formatter import BasePowertoolsFormatter


class CustomFormatter(BasePowertoolsFormatter):
    def __init__(self, log_record_order: Optional[List[str]] = None, *args, **kwargs):
        self.log_record_order = log_record_order or ["level", "location", "message", "timestamp"]
        self.log_format = dict.fromkeys(self.log_record_order)
        super().__init__(*args, **kwargs)

    def append_keys(self, **additional_keys):
        # also used by `inject_lambda_context` decorator
        self.log_format.update(additional_keys)

    def remove_keys(self, keys: Iterable[str]):
        for key in keys:
            self.log_format.pop(key, None)

    def clear_state(self):
        self.log_format = dict.fromkeys(self.log_record_order)

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        """Format logging record as structured JSON str"""
        return json.dumps(
            {
                "event": super().format(record),
                "timestamp": self.formatTime(record),
                "my_default_key": "test",
                **self.log_format,
            }
        )


logger = Logger(service="payment", logger_formatter=CustomFormatter())


@logger.inject_lambda_context
def handler(event, context):
    logger.info("Collecting payment")
