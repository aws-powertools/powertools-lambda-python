import logging
from pathlib import Path

from aws_lambda_powertools import Logger

log_file = Path("/tmp/log.json")
log_file_handler = logging.FileHandler(filename=log_file)

logger = Logger(service="payment", logger_handler=log_file_handler)

logger.info("hello world")
