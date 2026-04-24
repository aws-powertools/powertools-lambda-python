import asyncio

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.middlewares import NextMiddleware

app = APIGatewayRestResolver()
logger = Logger()


def inject_correlation_id(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:  # (1)!
    request_id = app.current_event.request_context.request_id
    app.append_context(correlation_id=request_id)
    logger.set_correlation_id(request_id)

    result = next_middleware(app)

    result.headers["x-correlation-id"] = request_id
    return result


@app.get("/todos", middlewares=[inject_correlation_id])
async def get_todos():  # (2)!
    await asyncio.sleep(0)
    return {"todos": []}


def lambda_handler(event, context):
    return asyncio.run(app.resolve_async(event, context))
