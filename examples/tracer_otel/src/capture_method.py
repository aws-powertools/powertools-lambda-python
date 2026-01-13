from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

tracer = TracerOpenTelemetry(mode="auto")


@tracer.capture_method
def process_payment(payment_id: str) -> dict:
    return {"payment_id": payment_id, "status": "processed"}


@tracer.capture_lambda_handler
def lambda_handler(event, context):
    result = process_payment(event.get("payment_id", "123"))
    return {"statusCode": 200, "body": result}
