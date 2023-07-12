from aws_lambda_powertools import Logger

logger = Logger(service="payment")
logger.info("Local time")

logger_in_utc = Logger(service="order", utc=True)
logger_in_utc.info("GMT time zone")
