import asyncio

from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

tracer = TracerOpenTelemetry(mode="auto")


@tracer.capture_method
async def async_get_user(user_id: str) -> dict:
    await asyncio.sleep(0.1)  # Simulate async I/O
    return {"user_id": user_id, "name": "John Doe"}


@tracer.capture_lambda_handler
def lambda_handler(event, context):
    user = asyncio.run(async_get_user(event.get("user_id", "123")))
    return {"statusCode": 200, "body": user}
