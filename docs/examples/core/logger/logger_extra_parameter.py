from aws_lambda_powertools import Logger

logger = Logger(service="payment")

fields = {"request_id": "1123"}
logger.info("Collecting payment", extra=fields)
