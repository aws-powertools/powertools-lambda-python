import logging

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import utils

logger = Logger()

external_logger = logging.getLogger()

utils.copy_config_to_registered_loggers(source_logger=logger)
external_logger.info("test message")
