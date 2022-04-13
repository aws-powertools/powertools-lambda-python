from aws_lambda_powertools import Logger

logger = Logger(service="payment")


@logger.inject_lambda_context(clear_state=True)
def handler(event, context):
    if event.get("special_key"):
        # Should only be available in the first request log
        # as the second request doesn't contain `special_key`
        logger.append_keys(debugging_key="value")

    logger.info("Collecting payment")
