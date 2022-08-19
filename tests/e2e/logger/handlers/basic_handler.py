from aws_lambda_powertools import Logger

logger = Logger()


@logger.inject_lambda_context
def lambda_handler(event, context):
    message, append_keys = event.get("message", ""), event.get("append_keys", {})
    logger.append_keys(**append_keys)
    logger.info(message)
    return "success"
