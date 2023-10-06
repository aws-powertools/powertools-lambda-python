import requests

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter

ENDPOINT = "http://httpbin.org/status/500"
logger = Logger(logger_formatter=LambdaPowertoolsFormatter(serialize_stacktrace=True))


def lambda_handler(event: dict, context: LambdaContext) -> str:
    try:
        ret = requests.get(ENDPOINT)
        ret.raise_for_status()
    except requests.HTTPError as e:
        logger.exception(e)
        raise RuntimeError("Unable to fullfil request") from e

    return "hello world"
