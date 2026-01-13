from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

# Configure custom TracerProvider with OTLP exporter
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))

tracer = TracerOpenTelemetry(mode="manual", tracer_provider=provider, service="my-service")


@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return {"statusCode": 200, "body": "Hello, World!"}
