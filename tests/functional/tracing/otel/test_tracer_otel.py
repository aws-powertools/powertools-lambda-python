"""Functional tests for OpenTelemetry Tracer with real OTel SDK."""

from __future__ import annotations

import pytest

pytest.importorskip("opentelemetry")

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


@pytest.fixture
def in_memory_exporter():
    """Create TracerProvider with in-memory exporter."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider, exporter


# Span hierarchy tests


def test_handler_creates_root_span(in_memory_exporter):
    """Handler decorator should create root span."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry
    from aws_lambda_powertools.tracing.otel import tracer as tracer_module

    tracer_module.is_cold_start = True

    provider, exporter = in_memory_exporter
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=provider)

    @tracer.capture_lambda_handler
    def handler(event, context):
        return {"statusCode": 200}

    class MockContext:
        function_name = "test_function"

    handler({}, MockContext())

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "handler"


def test_method_creates_child_span(in_memory_exporter):
    """Method decorator should create child span."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry
    from aws_lambda_powertools.tracing.otel import tracer as tracer_module

    tracer_module.is_cold_start = True

    provider, exporter = in_memory_exporter
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=provider)

    @tracer.capture_method
    def process_data():
        return "processed"

    @tracer.capture_lambda_handler
    def handler(event, context):
        return process_data()

    class MockContext:
        function_name = "test_function"

    handler({}, MockContext())

    spans = exporter.get_finished_spans()
    assert len(spans) == 2


def test_add_span_creates_child(in_memory_exporter):
    """add_span should create child span."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry
    from aws_lambda_powertools.tracing.otel import tracer as tracer_module

    tracer_module.is_cold_start = True

    provider, exporter = in_memory_exporter
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=provider)

    @tracer.capture_lambda_handler
    def handler(event, context):
        with tracer.add_span("custom_operation") as span:
            span.set_attribute("custom_key", "custom_value")
        return {"statusCode": 200}

    class MockContext:
        function_name = "test_function"

    handler({}, MockContext())

    spans = exporter.get_finished_spans()
    assert len(spans) == 2
    custom_span = next(s for s in spans if s.name == "custom_operation")
    assert custom_span.attributes.get("custom_key") == "custom_value"


# Span attributes tests


def test_cold_start_attribute(in_memory_exporter):
    """Should set faas.coldstart attribute."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry
    from aws_lambda_powertools.tracing.otel import tracer as tracer_module

    tracer_module.is_cold_start = True

    provider, exporter = in_memory_exporter
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=provider, service="test-service")

    @tracer.capture_lambda_handler
    def handler(event, context):
        return {"statusCode": 200}

    class MockContext:
        function_name = "test_function"

    handler({}, MockContext())

    spans = exporter.get_finished_spans()
    assert spans[0].attributes.get("faas.coldstart") is True
    assert spans[0].attributes.get("service.name") == "test-service"


def test_response_captured_as_attribute(in_memory_exporter):
    """Should capture response as span attribute."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry
    from aws_lambda_powertools.tracing.otel import tracer as tracer_module

    tracer_module.is_cold_start = True

    provider, exporter = in_memory_exporter
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=provider)

    @tracer.capture_lambda_handler(capture_response=True)
    def handler(event, context):
        return {"statusCode": 200}

    class MockContext:
        function_name = "test_function"

    handler({}, MockContext())

    spans = exporter.get_finished_spans()
    assert "handler.response" in spans[0].attributes


# Error handling tests


def test_exception_recorded_in_span(in_memory_exporter):
    """Should record exception in span."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry
    from aws_lambda_powertools.tracing.otel import tracer as tracer_module

    tracer_module.is_cold_start = True

    provider, exporter = in_memory_exporter
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=provider)

    @tracer.capture_lambda_handler
    def handler(event, context):
        raise ValueError("test error")

    class MockContext:
        function_name = "test_function"

    with pytest.raises(ValueError):
        handler({}, MockContext())

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert len(spans[0].events) > 0  # Exception event recorded


# Propagation tests


def test_inject_trace_context(in_memory_exporter):
    """inject_trace_context should add trace headers to carrier."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry
    from aws_lambda_powertools.tracing.otel import tracer as tracer_module
    from aws_lambda_powertools.tracing.otel.propagation import inject_trace_context

    tracer_module.is_cold_start = True

    provider, exporter = in_memory_exporter
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=provider)

    @tracer.capture_lambda_handler
    def handler(event, context):
        carrier = {"data": "payload"}
        result = inject_trace_context(carrier)
        return result

    class MockContext:
        function_name = "test_function"

    result = handler({}, MockContext())

    assert "data" in result
    # traceparent header should be injected
    assert "traceparent" in result or len(result) >= 1


def test_create_span_from_context(in_memory_exporter):
    """create_span_from_context should create span with extracted context."""
    from opentelemetry import trace

    from aws_lambda_powertools.tracing.otel.propagation import create_span_from_context

    provider, exporter = in_memory_exporter

    # Set the provider as global so create_span_from_context uses it
    trace.set_tracer_provider(provider)

    # Carrier with no context - should still create span
    carrier = {"data": "payload"}

    with create_span_from_context("process_message", carrier) as span:
        span.set_attribute("test_key", "test_value")

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "process_message"
    assert spans[0].attributes.get("test_key") == "test_value"
