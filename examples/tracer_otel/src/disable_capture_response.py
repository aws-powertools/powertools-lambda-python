from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

tracer = TracerOpenTelemetry(mode="auto")


@tracer.capture_lambda_handler(capture_response=False)
def lambda_handler(event, context):
    # Response won't be captured in span attributes
    return {"statusCode": 200, "body": "sensitive data"}
