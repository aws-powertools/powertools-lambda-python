from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def lambda_handler(event: dict, context: LambdaContext) -> str:
    request = APIGatewayProxyEvent(event)

    logger.set_correlation_id(request.request_context.request_id)
    logger.info("Collecting payment")

    return "hello world"
