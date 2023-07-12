import asyncio
from uuid import uuid4

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()


@tracer.capture_method
async def async_get_users():
    return [{"id": f"{uuid4()}"} for _ in range(5)]


def lambda_handler(event: dict, context: LambdaContext):
    tracer.service = event.get("service")
    return asyncio.run(async_get_users())
