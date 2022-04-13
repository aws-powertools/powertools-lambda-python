from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

logger = Logger(service="payment")


def handler(event, context):
    event = APIGatewayProxyEvent(event)
    logger.set_correlation_id(event.request_context.request_id)
    logger.info("Collecting payment")
