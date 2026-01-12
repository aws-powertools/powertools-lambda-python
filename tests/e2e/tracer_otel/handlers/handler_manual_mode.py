"""Lambda handler for E2E tests - Manual mode."""

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

# Configure TracerProvider
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))

tracer = TracerOpenTelemetry(mode="manual", tracer_provider=provider)


@tracer.capture_method
def process_data(data: dict) -> dict:
    return {"processed": True, "input": data}


@tracer.capture_lambda_handler
def handler(event, context):
    with tracer.add_span("business_logic") as span:
        span.set_attribute("event_size", len(str(event)))
        result = process_data(event)

    return {"statusCode": 200, "body": result}
