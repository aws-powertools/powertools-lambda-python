import os

from aws_lambda_powertools import Logger

logger = Logger()

MESSAGE = os.environ["MESSAGE"]
ADDITIONAL_KEY = os.environ["ADDITIONAL_KEY"]


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    logger.debug(MESSAGE)
    logger.info(MESSAGE)
    logger.append_keys(**{ADDITIONAL_KEY: "test"})
    logger.info(MESSAGE)
    return "success"
