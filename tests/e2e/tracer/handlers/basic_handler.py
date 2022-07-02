import asyncio
import os

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer(service="e2e-tests-app")

ANNOTATION_KEY = os.environ["ANNOTATION_KEY"]
ANNOTATION_VALUE = os.environ["ANNOTATION_VALUE"]
ANNOTATION_ASYNC_VALUE = os.environ["ANNOTATION_ASYNC_VALUE"]


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext):
    tracer.put_metadata(key=ANNOTATION_KEY, value=ANNOTATION_VALUE)
    return asyncio.run(collect_payment())


@tracer.capture_method
async def collect_payment() -> str:
    tracer.put_metadata(key=ANNOTATION_KEY, value=ANNOTATION_ASYNC_VALUE)
    return "success"
