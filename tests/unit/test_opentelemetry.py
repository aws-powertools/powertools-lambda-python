from unittest.mock import MagicMock

from aws_lambda_powertools.tracing import OpenTelemetryProvider, OpenTelemetrySegment, Tracer


def test_opentelemetry_segment_attributes():
    mock_span = MagicMock()
    segment = OpenTelemetrySegment(mock_span)

    segment.put_annotation("key_ann", "val_ann")
    mock_span.set_attribute.assert_called_with("key_ann", "val_ann")

    segment.put_metadata("key_meta", {"data": 123}, namespace="test_ns")
    mock_span.set_attribute.assert_called_with("test_ns.key_meta", "{'data': 123}")


def test_opentelemetry_segment_exception():
    mock_span = MagicMock()
    segment = OpenTelemetrySegment(mock_span)
    err = ValueError("test error")

    segment.add_exception(err)
    mock_span.record_exception.assert_called_with(err)


def test_opentelemetry_provider_subsegment():
    mock_tracer = MagicMock()
    mock_span = MagicMock()
    mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

    provider = OpenTelemetryProvider(tracer=mock_tracer)

    with provider.in_subsegment("my_subsegment") as sub:
        assert isinstance(sub, OpenTelemetrySegment)
        assert sub.span == mock_span

    mock_tracer.start_as_current_span.assert_called_with("my_subsegment")


def test_tracer_with_opentelemetry_provider():
    mock_tracer = MagicMock()
    mock_span = MagicMock()
    mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

    provider = OpenTelemetryProvider(tracer=mock_tracer)
    tracer = Tracer(service="test-service", provider=provider, disabled=False)

    assert tracer.provider == provider

    @tracer.capture_method
    def sample_func():
        return "ok"

    res = sample_func()
    assert res == "ok"
