from logging_inheritance_module import inject_payment_id

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

# NOTE: explicit service name differs from Child
# meaning we will have two Logger instances with different state
# and an orphan child logger who won't be able to manipulate state
logger = Logger(service="payment")


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> str:
    inject_payment_id(context=event)

    return "hello world"
