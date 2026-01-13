from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

tracer = TracerOpenTelemetry(mode="auto")


@tracer.capture_lambda_handler
def lambda_handler(event, context):
    with tracer.add_span("process_order") as span:
        span.set_attribute("order_id", event.get("order_id", "unknown"))
        span.set_attribute("customer_tier", "premium")
        # Process order logic here
        result = {"order_id": event.get("order_id"), "status": "completed"}

    return {"statusCode": 200, "body": result}
