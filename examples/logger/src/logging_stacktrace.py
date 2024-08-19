from __future__ import annotations

from typing import TYPE_CHECKING

import requests

from aws_lambda_powertools import Logger

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

ENDPOINT = "http://httpbin.org/status/500"
logger = Logger(serialize_stacktrace=True)


def lambda_handler(event: dict, context: LambdaContext) -> str:
    try:
        ret = requests.get(ENDPOINT)
        ret.raise_for_status()
    except requests.HTTPError as e:
        logger.exception(e)
        raise RuntimeError("Unable to fullfil request") from e

    return "hello world"
