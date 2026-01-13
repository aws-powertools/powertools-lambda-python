import json

from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry
from aws_lambda_powertools.tracing.otel.propagation import inject_trace_context

tracer = TracerOpenTelemetry(mode="auto")


@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """Producer: Inject trace context into SQS message."""
    message = {"order_id": "12345", "amount": 99.99}

    # Inject trace context for downstream consumers
    message_with_context = inject_trace_context(message)

    # Send to SQS with: sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message_with_context))

    return {"statusCode": 200, "body": json.dumps(message_with_context)}
