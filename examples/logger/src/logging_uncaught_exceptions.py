import requests

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

ENDPOINT = "http://httpbin.org/status/500"
logger = Logger(log_uncaught_exceptions=True)


def lambda_handler(event: dict, context: LambdaContext) -> str:
    ret = requests.get(ENDPOINT)
    # HTTP 4xx/5xx status will lead to requests.HTTPError
    # Logger will log this exception before this program exits non-successfully
    ret.raise_for_status()

    return "hello world"
