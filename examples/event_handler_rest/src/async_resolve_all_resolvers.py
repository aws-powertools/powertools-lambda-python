import asyncio

from aws_lambda_powertools.event_handler import (
    ALBResolver,
    APIGatewayHttpResolver,
    APIGatewayRestResolver,
)

rest_app = APIGatewayRestResolver()  # (1)!
http_app = APIGatewayHttpResolver()  # (2)!
alb_app = ALBResolver()  # (3)!


@rest_app.get("/hello")
@http_app.get("/hello")
@alb_app.get("/hello")
async def hello():
    await asyncio.sleep(0)
    return {"message": "hello from async"}


def rest_handler(event, context):
    return asyncio.run(rest_app.resolve_async(event, context))


def http_handler(event, context):
    return asyncio.run(http_app.resolve_async(event, context))


def alb_handler(event, context):
    return asyncio.run(alb_app.resolve_async(event, context))
