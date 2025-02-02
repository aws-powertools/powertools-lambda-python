from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger(service="payment", level="DEBUG")


def lambda_handler(event: dict, context: LambdaContext) -> str:
    try:
        logger.append_keys(order_id="12345")
        logger.info("Starting order processing")
    finally:
        logger.info("Final state before clearing")
        logger.clear_state()
        logger.info("State after clearing - only show default keys")
    return "Completed"
