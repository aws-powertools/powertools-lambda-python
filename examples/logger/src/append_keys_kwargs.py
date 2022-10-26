from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def handler(event: dict, context: LambdaContext) -> str:
    logger.info("Collecting payment", request_id="1123")

    return "hello world"
