from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> str:
    logger.info("Collecting payment")

    # You can log entire objects too
    logger.info({"operation": "collect_payment", "charge_id": event["charge_id"]})
    return "hello world"
