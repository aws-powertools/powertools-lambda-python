from aws_lambda_powertools import Logger

logger = Logger(service="payment")

try:
    raise ValueError("something went wrong")
except Exception:
    logger.exception("Received an exception")
