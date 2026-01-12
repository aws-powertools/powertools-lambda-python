"""OpenTelemetry Tracer for AWS Lambda Powertools"""

from aws_lambda_powertools.tracing.otel.propagation import create_span_from_context, inject_trace_context
from aws_lambda_powertools.tracing.otel.tracer import TracerOpenTelemetry

__all__ = ["TracerOpenTelemetry", "inject_trace_context", "create_span_from_context"]
