import os
import time

from aws_lambda_powertools import Logger

logger_in_utc = Logger(service="payment")
logger_in_utc.info("Logging with default AWS Lambda timezone: UTC time")

os.environ["TZ"] = "US/Eastern"
time.tzset()  # (1)!

logger = Logger(service="order")
logger.info("Logging with US Eastern timezone")
