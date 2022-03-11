from aws_lambda_powertools import Logger

logger = Logger(service="payment")


def handler(event, context):
    logger.set_correlation_id(event["requestContext"]["requestId"])
    logger.info("Collecting payment")
