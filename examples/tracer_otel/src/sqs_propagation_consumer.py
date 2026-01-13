import json

from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry
from aws_lambda_powertools.tracing.otel.propagation import create_span_from_context

tracer = TracerOpenTelemetry(mode="auto")


@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """Consumer: Extract trace context from SQS message."""
    for record in event.get("Records", []):
        message = json.loads(record["body"])

        # Continue the trace from the producer
        with create_span_from_context("process_order", message) as span:
            span.set_attribute("order_id", message.get("order_id"))
            # Process the order

    return {"statusCode": 200}
