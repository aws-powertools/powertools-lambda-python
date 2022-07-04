from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def handler(event: dict, context: LambdaContext) -> str:
    order_id = event.get("order_id")

    # this will ensure order_id key always has the latest value before logging
    # alternative, you can use `clear_state=True` parameter in @inject_lambda_context
    logger.append_keys(order_id=order_id)
    logger.info("Collecting payment")

    return "hello world"
