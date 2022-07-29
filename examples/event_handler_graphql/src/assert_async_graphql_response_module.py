import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

import asyncio
from typing import List

import aiohttp

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.tracing import aiohttp_trace_config
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = AppSyncResolver()


class Todo(TypedDict, total=False):
    id: str  # noqa AA03 VNE003, required due to GraphQL Schema
    userId: str
    title: str
    completed: bool


@app.resolver(type_name="Query", field_name="listTodos")
async def list_todos() -> List[Todo]:
    async with aiohttp.ClientSession(trace_configs=[aiohttp_trace_config()]) as session:
        async with session.get("https://jsonplaceholder.typicode.com/todos") as resp:
            result: List[Todo] = await resp.json()
            return result[:2]  # first two results to demo assertion


@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    result = app.resolve(event, context)

    return asyncio.run(result)
