import requests

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

ENDPOINT = "https://httpbin.org/status/500"
logger = Logger(serialize_stacktrace=False)


def lambda_handler(event: dict, context: LambdaContext) -> str:
    try:
        ret = requests.get(ENDPOINT)
        ret.raise_for_status()
    except requests.HTTPError as e:
        e.add_note("Can't connect to the endpoint")  # type: ignore[attr-defined]
        logger.exception(e)
        raise RuntimeError("Unable to fullfil request") from e

    return "hello world"
