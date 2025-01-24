from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger(service="example_service")


def lambda_handler(event: dict, context: LambdaContext) -> str:
    with logger.append_context_keys(user_id="123", operation="process"):
        logger.info("Log with context")

    logger.info("Log without context")

    return "hello world"
