from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.formatters import DatadogLogFormatter

logger = Logger(service="payment", logger_formatter=DatadogLogFormatter())
logger.info("hello")
