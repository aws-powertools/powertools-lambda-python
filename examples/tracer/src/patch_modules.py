from __future__ import annotations

from typing import TYPE_CHECKING

import requests

from aws_lambda_powertools import Tracer

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

MODULES = ["requests"]

tracer = Tracer(patch_modules=MODULES)


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> str:
    ret = requests.get("https://httpbin.org/get")
    ret.raise_for_status()

    return ret.json()
