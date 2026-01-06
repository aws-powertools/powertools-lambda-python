"""Tests for Metrics with DurableContext support."""

import json
from collections import namedtuple
from unittest.mock import Mock

import pytest

from aws_lambda_powertools import Metrics

# Reset cold start flag before each test
from aws_lambda_powertools.metrics.provider import cold_start
from aws_lambda_powertools.utilities.typing import DurableContextProtocol


def capture_metrics_output(capsys):
    return json.loads(capsys.readouterr().out.strip())


def capture_metrics_output_multiple_emf_objects(capsys):
    return [json.loads(line.strip()) for line in capsys.readouterr().out.split("\n") if line]


def reset_cold_start_flag():
    cold_start.is_cold_start = True


@pytest.fixture
def lambda_context():
    lambda_context = {
        "function_name": "test",
        "memory_limit_in_mb": 128,
        "invoked_function_arn": "arn:aws:lambda:eu-west-1:809313241:function:test",
        "aws_request_id": "52fdfc07-2182-154f-163f-5f0f9a621d72",
    }
    return namedtuple("LambdaContext", lambda_context.keys())(*lambda_context.values())


@pytest.fixture
def durable_context(lambda_context):
    """Create a mock DurableContext with embedded Lambda context."""
    durable_ctx = Mock(spec=DurableContextProtocol)
    durable_ctx.lambda_context = lambda_context
    durable_ctx.state = Mock(operations=[{"id": "op1"}])
    return durable_ctx


@pytest.fixture
def lambda_context_with_function_name():
    """Create a simple lambda context with function_name."""
    LambdaContext = namedtuple("LambdaContext", "function_name")
    return LambdaContext("test_function")


def test_log_metrics_with_durable_context_basic(capsys, namespace, service, durable_context):
    """Test that log_metrics works with DurableContext."""
    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)

    # WHEN log_metrics decorator is used with a handler that receives DurableContext
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        my_metrics.add_metric(name="test_metric", value=1.0, unit="Count")

    lambda_handler({}, durable_context)

    # THEN metrics should be emitted successfully
    output = capture_metrics_output(capsys)

    assert output["test_metric"] == [1.0]
    assert output["service"] == service


def test_log_metrics_capture_cold_start_with_durable_context(capsys, namespace, service):
    """Test that capture_cold_start_metric works with DurableContext."""
    reset_cold_start_flag()

    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)

    # Create a DurableContext with embedded Lambda context
    LambdaContext = namedtuple("LambdaContext", "function_name")
    lambda_ctx = LambdaContext("durable_test_function")

    durable_ctx = Mock(spec=DurableContextProtocol)
    durable_ctx.lambda_context = lambda_ctx
    durable_ctx.state = Mock(operations=[{"id": "op1"}])

    # WHEN log_metrics is used with capture_cold_start_metric and DurableContext
    @my_metrics.log_metrics(capture_cold_start_metric=True)
    def lambda_handler(evt, context):
        my_metrics.add_metric(name="test_metric", value=1.0, unit="Count")

    lambda_handler({}, durable_ctx)

    # THEN ColdStart metric should be captured with the function name from unwrapped context
    outputs = capture_metrics_output_multiple_emf_objects(capsys)

    # Cold start is in a separate EMF blob
    cold_start_output = outputs[0]
    assert cold_start_output["ColdStart"] == [1.0]
    assert cold_start_output["function_name"] == "durable_test_function"
    assert cold_start_output["service"] == service


def test_log_metrics_capture_cold_start_with_durable_context_explicit_function_name(capsys, namespace, service):
    """Test capture_cold_start_metric with explicit function_name and DurableContext."""
    reset_cold_start_flag()

    # GIVEN Metrics is initialized with explicit function_name
    my_metrics = Metrics(service=service, namespace=namespace, function_name="explicit_function")

    # Create a DurableContext
    LambdaContext = namedtuple("LambdaContext", "function_name")
    lambda_ctx = LambdaContext("context_function")

    durable_ctx = Mock(spec=DurableContextProtocol)
    durable_ctx.lambda_context = lambda_ctx
    durable_ctx.state = Mock(operations=[{"id": "op1"}])

    # WHEN log_metrics is used with capture_cold_start_metric
    @my_metrics.log_metrics(capture_cold_start_metric=True)
    def lambda_handler(evt, context):
        pass

    lambda_handler({}, durable_ctx)

    # THEN explicit function_name should take priority
    output = capture_metrics_output(capsys)

    assert output.get("function_name") == "explicit_function"


def test_log_metrics_with_standard_context_still_works(capsys, namespace, service, lambda_context):
    """Test that standard Lambda context still works (regression test)."""
    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)

    # WHEN log_metrics decorator is used with standard LambdaContext
    @my_metrics.log_metrics
    def lambda_handler(evt, context):
        my_metrics.add_metric(name="regression_test", value=42.0, unit="Count")

    lambda_handler({}, lambda_context)

    # THEN metrics should be emitted successfully
    output = capture_metrics_output(capsys)

    assert output["regression_test"] == [42.0]
    assert output["service"] == service


def test_log_metrics_capture_cold_start_standard_context_still_works(capsys, namespace, service):
    """Test that capture_cold_start_metric with standard context still works (regression test)."""
    reset_cold_start_flag()

    # GIVEN Metrics is initialized
    my_metrics = Metrics(service=service, namespace=namespace)

    LambdaContext = namedtuple("LambdaContext", "function_name")
    standard_context = LambdaContext("standard_function")

    # WHEN log_metrics is used with capture_cold_start_metric and standard context
    @my_metrics.log_metrics(capture_cold_start_metric=True)
    def lambda_handler(evt, context):
        pass

    lambda_handler({}, standard_context)

    # THEN ColdStart metric should be captured
    output = capture_metrics_output(capsys)

    assert "ColdStart" in output or output.get("ColdStart") == [1.0]
    assert output.get("function_name") == "standard_function"
