"""Unit tests for OpenTelemetry Tracer."""

from __future__ import annotations

from unittest import mock

import pytest


@pytest.fixture
def reset_cold_start():
    """Reset cold start state before each test."""
    from aws_lambda_powertools.tracing.otel import tracer as tracer_module

    tracer_module.is_cold_start = True
    yield
    tracer_module.is_cold_start = True


@pytest.fixture
def mock_tracer_provider():
    """Create a mock TracerProvider."""
    mock_span = mock.MagicMock()
    mock_span.__enter__ = mock.MagicMock(return_value=mock_span)
    mock_span.__exit__ = mock.MagicMock(return_value=False)

    mock_tracer = mock.MagicMock()
    mock_tracer.start_as_current_span.return_value = mock_span

    mock_provider = mock.MagicMock()
    mock_provider.get_tracer.return_value = mock_tracer

    return mock_provider, mock_tracer, mock_span


# Init tests


def test_auto_mode_raises_if_tracer_provider_given():
    """Auto mode should raise error if tracer_provider is provided."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider = mock.MagicMock()

    with pytest.raises(ValueError, match="tracer_provider cannot be provided in auto mode"):
        TracerOpenTelemetry(mode="auto", tracer_provider=mock_provider)


def test_manual_mode_uses_provided_tracer_provider(mock_tracer_provider):
    """Manual mode should use provided TracerProvider."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, _, _ = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    assert tracer.provider == mock_provider


def test_manual_mode_creates_vanilla_provider_if_none_given():
    """Manual mode should create vanilla TracerProvider if none provided."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    with mock.patch("opentelemetry.sdk.trace.TracerProvider") as mock_sdk:
        mock_sdk.return_value = mock.MagicMock()
        TracerOpenTelemetry(mode="manual")
        mock_sdk.assert_called_once()


def test_disabled_mode():
    """Disabled tracer should not create provider."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    tracer = TracerOpenTelemetry(mode="manual", disabled=True)

    assert tracer.disabled is True
    assert tracer._tracer_provider is None


def test_service_from_env_var(monkeypatch):
    """Service name should fall back to environment variable."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    monkeypatch.setenv("POWERTOOLS_SERVICE_NAME", "test-service")

    tracer = TracerOpenTelemetry(mode="manual", disabled=True)

    assert tracer.service == "test-service"


def test_disabled_from_env_var(monkeypatch):
    """Disabled should fall back to environment variable."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    monkeypatch.setenv("POWERTOOLS_TRACE_DISABLED", "true")

    tracer = TracerOpenTelemetry(mode="manual")

    assert tracer.disabled is True


# capture_lambda_handler tests


def test_creates_span_for_handler(mock_tracer_provider, reset_cold_start):
    """Should create span for Lambda handler."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, mock_tracer, _ = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    @tracer.capture_lambda_handler
    def handler(event, context):
        return {"statusCode": 200}

    result = handler({}, mock.MagicMock())

    assert result == {"statusCode": 200}
    mock_tracer.start_as_current_span.assert_called_once()


def test_adds_cold_start_attribute(mock_tracer_provider, reset_cold_start):
    """Should add faas.coldstart attribute."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, _, mock_span = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    @tracer.capture_lambda_handler
    def handler(event, context):
        return {"statusCode": 200}

    handler({}, mock.MagicMock())

    mock_span.set_attribute.assert_any_call("faas.coldstart", True)


def test_cold_start_false_on_second_invocation(mock_tracer_provider, reset_cold_start):
    """Cold start should be False on second invocation."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, _, mock_span = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    @tracer.capture_lambda_handler
    def handler(event, context):
        return {"statusCode": 200}

    handler({}, mock.MagicMock())
    mock_span.reset_mock()
    handler({}, mock.MagicMock())

    mock_span.set_attribute.assert_any_call("faas.coldstart", False)


def test_handler_disabled_passes_through(reset_cold_start):
    """Disabled tracer should pass through without tracing."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    tracer = TracerOpenTelemetry(mode="manual", disabled=True)

    @tracer.capture_lambda_handler
    def handler(event, context):
        return {"statusCode": 200}

    result = handler({}, mock.MagicMock())

    assert result == {"statusCode": 200}


def test_captures_exception(mock_tracer_provider, reset_cold_start):
    """Should record exception when handler raises."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, _, mock_span = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    @tracer.capture_lambda_handler
    def handler(event, context):
        raise ValueError("test error")

    with pytest.raises(ValueError):
        handler({}, mock.MagicMock())

    mock_span.record_exception.assert_called_once()


# capture_method tests


def test_sync_function(mock_tracer_provider):
    """Should trace sync function."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, mock_tracer, _ = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    @tracer.capture_method
    def my_function():
        return "result"

    result = my_function()

    assert result == "result"
    mock_tracer.start_as_current_span.assert_called_once()


def test_async_function(mock_tracer_provider):
    """Should trace async function."""
    import asyncio

    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, mock_tracer, _ = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    @tracer.capture_method
    async def my_async_function():
        return "async result"

    result = asyncio.run(my_async_function())

    assert result == "async result"
    mock_tracer.start_as_current_span.assert_called_once()


def test_generator_function(mock_tracer_provider):
    """Should trace generator function."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, mock_tracer, _ = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    @tracer.capture_method
    def my_generator():
        yield 1
        yield 2

    result = list(my_generator())

    assert result == [1, 2]
    mock_tracer.start_as_current_span.assert_called_once()


def test_method_disabled_passes_through():
    """Disabled tracer should pass through without tracing."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    tracer = TracerOpenTelemetry(mode="manual", disabled=True)

    @tracer.capture_method
    def my_function():
        return "result"

    result = my_function()

    assert result == "result"


# add_span tests


def test_creates_child_span(mock_tracer_provider):
    """Should create child span."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, mock_tracer, _ = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    with tracer.add_span("test_span") as span:
        span.set_attribute("key", "value")

    mock_tracer.start_as_current_span.assert_called_once_with(
        name="test_span",
        record_exception=True,
        set_status_on_exception=True,
    )


def test_add_span_disabled_yields_none():
    """Disabled tracer should yield None."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    tracer = TracerOpenTelemetry(mode="manual", disabled=True)

    with tracer.add_span("test_span") as span:
        assert span is None


# get_current_span tests


def test_get_current_span_returns_none_when_disabled():
    """Should return None when disabled."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    tracer = TracerOpenTelemetry(mode="manual", disabled=True)

    assert tracer.get_current_span() is None


def test_get_current_span_returns_current_span(mock_tracer_provider):
    """Should return current span from OTel context."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, _, _ = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    with mock.patch("opentelemetry.trace.get_current_span") as mock_get:
        mock_get.return_value = mock.MagicMock()
        span = tracer.get_current_span()

        mock_get.assert_called_once()
        assert span is not None


# Cold start with provisioned concurrency


def test_cold_start_false_with_provisioned_concurrency(monkeypatch, mock_tracer_provider, reset_cold_start):
    """Cold start should be False with provisioned concurrency."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    monkeypatch.setenv("AWS_LAMBDA_INITIALIZATION_TYPE", "provisioned-concurrency")

    mock_provider, _, mock_span = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    @tracer.capture_lambda_handler
    def handler(event, context):
        return {"statusCode": 200}

    handler({}, mock.MagicMock())

    mock_span.set_attribute.assert_any_call("faas.coldstart", False)


# Auto mode provider


def test_auto_mode_uses_global_provider():
    """Auto mode should use global TracerProvider."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    with mock.patch("opentelemetry.trace.get_tracer_provider") as mock_get:
        mock_provider = mock.MagicMock()
        mock_get.return_value = mock_provider

        tracer = TracerOpenTelemetry(mode="auto")
        provider = tracer.provider

        mock_get.assert_called_once()
        assert provider == mock_provider


# instrument_requests


def test_instrument_requests_disabled():
    """instrument_requests should do nothing when disabled."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    tracer = TracerOpenTelemetry(mode="manual", disabled=True)
    tracer.instrument_requests()  # Should not raise


def test_instrument_requests_import_error(mock_tracer_provider, caplog):
    """instrument_requests should warn on missing package."""
    import logging
    import sys

    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, _, _ = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    # Remove the module if it exists to simulate ImportError
    original = sys.modules.get("opentelemetry.instrumentation.requests")
    sys.modules["opentelemetry.instrumentation.requests"] = None

    try:
        with caplog.at_level(logging.WARNING):
            tracer.instrument_requests()
    finally:
        if original:
            sys.modules["opentelemetry.instrumentation.requests"] = original
        else:
            sys.modules.pop("opentelemetry.instrumentation.requests", None)


# capture_method with capture_response=False


def test_capture_method_no_response(mock_tracer_provider):
    """capture_method should not capture response when disabled."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, _, mock_span = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    @tracer.capture_method(capture_response=False)
    def my_function():
        return "result"

    result = my_function()

    assert result == "result"
    # Should not have response attribute set
    response_calls = [c for c in mock_span.set_attribute.call_args_list if "response" in str(c)]
    assert len(response_calls) == 0


# capture_lambda_handler with capture_error=False


def test_handler_no_error_capture(mock_tracer_provider, reset_cold_start):
    """Handler should not record exception when capture_error=False."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, _, mock_span = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    @tracer.capture_lambda_handler(capture_error=False)
    def handler(event, context):
        raise ValueError("test error")

    with pytest.raises(ValueError):
        handler({}, mock.MagicMock())

    mock_span.record_exception.assert_not_called()


# Generator disabled pass-through


def test_generator_disabled_passes_through():
    """Disabled tracer should pass through generator without tracing."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    tracer = TracerOpenTelemetry(mode="manual", disabled=True)

    @tracer.capture_method
    def my_generator():
        yield 1
        yield 2

    result = list(my_generator())

    assert result == [1, 2]


# Service from Lambda function name


def test_service_from_lambda_function_name(monkeypatch):
    """Service name should fall back to Lambda function name."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    monkeypatch.delenv("POWERTOOLS_SERVICE_NAME", raising=False)
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "my-lambda-function")

    tracer = TracerOpenTelemetry(mode="manual", disabled=True)

    assert tracer.service == "my-lambda-function"


# Async disabled pass-through


def test_async_disabled_passes_through():
    """Disabled tracer should pass through async function without tracing."""
    import asyncio

    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    tracer = TracerOpenTelemetry(mode="manual", disabled=True)

    @tracer.capture_method
    async def my_async_function():
        return "async result"

    result = asyncio.run(my_async_function())

    assert result == "async result"


# Method exception capture


def test_method_captures_exception(mock_tracer_provider):
    """capture_method should record exception when method raises."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, _, mock_span = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    @tracer.capture_method
    def my_function():
        raise ValueError("test error")

    with pytest.raises(ValueError):
        my_function()

    mock_span.record_exception.assert_called_once()


# Async exception capture


def test_async_captures_exception(mock_tracer_provider):
    """capture_method should record exception when async method raises."""
    import asyncio

    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, _, mock_span = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    @tracer.capture_method
    async def my_async_function():
        raise ValueError("async error")

    with pytest.raises(ValueError):
        asyncio.run(my_async_function())

    mock_span.record_exception.assert_called_once()


# Generator exception capture


def test_generator_captures_exception(mock_tracer_provider):
    """capture_method should record exception when generator raises."""
    from aws_lambda_powertools.tracing.otel import TracerOpenTelemetry

    mock_provider, _, mock_span = mock_tracer_provider
    tracer = TracerOpenTelemetry(mode="manual", tracer_provider=mock_provider)

    @tracer.capture_method
    def my_generator():
        yield 1
        raise ValueError("generator error")

    with pytest.raises(ValueError):
        list(my_generator())

    mock_span.record_exception.assert_called_once()
