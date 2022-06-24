import os

from aws_lambda_powertools import Logger

logger = Logger()

MESSAGE = os.environ["MESSAGE"]
ADDITIONAL_KEY = os.environ["ADDITIONAL_KEY"]


def lambda_handler(event, context):
    logger.info(MESSAGE)
    logger.append_keys(**{ADDITIONAL_KEY: "test"})
    return "success"
