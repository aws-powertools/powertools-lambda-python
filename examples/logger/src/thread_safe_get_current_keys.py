from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> str:
    logger.info("Collecting payment")

    if "order" not in logger.thread_safe_get_current_keys():
        logger.thread_safe_append_keys(order=event.get("order"))

    return "hello world"
