import asyncio

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.logging import correlation_paths

tracer = Tracer(service="sample_resolver")
logger = Logger(service="sample_resolver")
app = AppSyncResolver()


@app.resolver(type_name="Query", field_name="listTodos")
async def list_todos():
    todos = await some_async_io_call()
    return todos


@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    result = app.resolve(event, context)

    return asyncio.run(result)
