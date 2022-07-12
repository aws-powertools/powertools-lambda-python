from logging_inheritance_module import inject_payment_id

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

# NOTE: explicit service name matches any new Logger
# because we're using POWERTOOLS_SERVICE_NAME env var
# but we could equally use the same string as service value, e.g. "payment"
logger = Logger()


@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> str:
    inject_payment_id(context=event)

    return "hello world"
