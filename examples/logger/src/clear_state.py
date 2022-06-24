from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@logger.inject_lambda_context(clear_state=True)
def handler(event: dict, context: LambdaContext) -> str:
    if event.get("special_key"):
        # Should only be available in the first request log
        # as the second request doesn't contain `special_key`
        logger.append_keys(debugging_key="value")

    logger.info("Collecting payment")

    return "hello world"
