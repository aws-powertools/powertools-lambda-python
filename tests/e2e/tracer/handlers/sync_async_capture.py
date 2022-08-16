import asyncio
from uuid import uuid4

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()


@tracer.capture_method
def get_todos():
    return [{"id": f"{uuid4()}", "completed": False} for _ in range(5)]


@tracer.capture_method
async def async_get_users():
    await asyncio.sleep(1)
    return [{"id": f"{uuid4()}"} for _ in range(5)]


def lambda_handler(event: dict, context: LambdaContext):
    # dummy data to avoid external endpoint impacting test itself
    return {"todos": get_todos(), "users": asyncio.run(async_get_users())}
