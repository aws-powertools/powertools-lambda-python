from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

tracer = TracerOpenTelemetry(mode="auto")


@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return {"statusCode": 200, "body": "Hello, World!"}
