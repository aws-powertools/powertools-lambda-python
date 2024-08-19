from __future__ import annotations

from typing import TYPE_CHECKING

import requests

from aws_lambda_powertools import Logger

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

ENDPOINT = "http://httpbin.org/status/500"
logger = Logger(log_uncaught_exceptions=True)


def lambda_handler(event: dict, context: LambdaContext) -> str:
    ret = requests.get(ENDPOINT)
    # HTTP 4xx/5xx status will lead to requests.HTTPError
    # Logger will log this exception before this program exits non-successfully
    ret.raise_for_status()

    return "hello world"
