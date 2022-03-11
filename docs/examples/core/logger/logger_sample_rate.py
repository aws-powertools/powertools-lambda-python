from aws_lambda_powertools import Logger

# Sample 10% of debug logs e.g. 0.1
logger = Logger(service="payment", sample_rate=0.1)


def handler(event, context):
    logger.debug("Verifying whether order_id is present")
    logger.info("Collecting payment")
