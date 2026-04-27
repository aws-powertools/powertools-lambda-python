import asyncio
from collections.abc import Callable

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response

app = APIGatewayRestResolver()
logger = Logger()


async def async_inject_correlation_id(app: APIGatewayRestResolver, next_middleware: Callable) -> Response:  # (1)!
    request_id = app.current_event.request_context.request_id
    app.append_context(correlation_id=request_id)
    logger.set_correlation_id(request_id)

    result = await next_middleware(app)  # (2)!

    result.headers["x-correlation-id"] = request_id
    return result


@app.get("/todos", middlewares=[async_inject_correlation_id])
async def get_todos():
    await asyncio.sleep(0)
    return {"todos": []}


def lambda_handler(event, context):
    return asyncio.run(app.resolve_async(event, context))
