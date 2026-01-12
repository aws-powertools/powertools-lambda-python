"""Lambda handler for E2E tests - Auto mode."""

from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

tracer = TracerOpenTelemetry(mode="auto")


@tracer.capture_method
def process_data(data: dict) -> dict:
    return {"processed": True, "input": data}


@tracer.capture_lambda_handler
def handler(event, context):
    with tracer.add_span("business_logic") as span:
        span.set_attribute("event_size", len(str(event)))
        result = process_data(event)

    return {"statusCode": 200, "body": result}
