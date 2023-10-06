import os
import time

from aws_lambda_powertools import Logger

logger = Logger(service="payment", utc=True)
logger.info("utf time")

os.environ["TZ"] = "US/Eastern"
time.tzset()  # (1)!

logger_in_utc = Logger(service="order")
logger_in_utc.info("US eastern time")
