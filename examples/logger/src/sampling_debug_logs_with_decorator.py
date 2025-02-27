from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

# Sample 10% of debug logs e.g. 0.1
logger = Logger(service="payment", sample_rate=0.1)


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext):
    logger.debug("Verifying whether order_id is present")
    logger.info("Collecting payment")

    return "hello world"
