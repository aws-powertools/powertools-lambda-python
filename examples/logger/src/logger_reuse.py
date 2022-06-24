from logger_reuse_payment import inject_payment_id

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> str:
    inject_payment_id(context=event)
    logger.info("Collecting payment")
    return "hello world"
