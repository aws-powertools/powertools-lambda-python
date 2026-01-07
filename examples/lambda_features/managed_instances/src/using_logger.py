from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info("Processing request")

    # Each concurrent request has its own logger instance
    # Correlation IDs are isolated per request
    logger.append_keys(order_id=event.get("order_id"))

    return {"statusCode": 200}
