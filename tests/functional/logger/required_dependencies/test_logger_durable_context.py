"""Tests for Logger with DurableContext support."""

import io
import json
import random
import string
from collections import namedtuple
from unittest.mock import Mock

import pytest

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import DurableContextProtocol


@pytest.fixture
def stdout():
    return io.StringIO()


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
def service_name():
    chars = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(chars) for _ in range(15))


def capture_logging_output(stdout):
    return json.loads(stdout.getvalue().strip())


def capture_multiple_logging_statements_output(stdout):
    return [json.loads(line.strip()) for line in stdout.getvalue().split("\n") if line]


@pytest.fixture
def durable_context(lambda_context):
    """Create a mock DurableContext with embedded Lambda context."""
    durable_ctx = Mock(spec=DurableContextProtocol)
    durable_ctx.lambda_context = lambda_context
    durable_ctx.state = Mock(operations=[{"id": "op1"}])
    return durable_ctx


def test_inject_lambda_context_with_durable_context(durable_context, stdout, service_name):
    """Test that inject_lambda_context works with DurableContext."""
    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

    # WHEN a lambda function is decorated with logger and receives DurableContext
    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Hello from durable function")

    handler({}, durable_context)

    # THEN lambda contextual info from the unwrapped context should be in the logs
    log = capture_logging_output(stdout)

    expected_logger_context_keys = (
        "function_name",
        "function_memory_size",
        "function_arn",
        "function_request_id",
    )
    for key in expected_logger_context_keys:
        assert key in log

    # Verify the actual values match the embedded lambda_context
    assert log["function_name"] == durable_context.lambda_context.function_name
    assert log["function_memory_size"] == durable_context.lambda_context.memory_limit_in_mb
    assert log["function_arn"] == durable_context.lambda_context.invoked_function_arn
    assert log["function_request_id"] == durable_context.lambda_context.aws_request_id
    assert log["message"] == "Hello from durable function"


def test_inject_lambda_context_with_durable_context_log_event(durable_context, stdout, service_name):
    """Test that inject_lambda_context with log_event=True works with DurableContext."""
    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

    test_event = {"test_key": "test_value"}

    # WHEN a lambda function is decorated with log_event=True and receives DurableContext
    @logger.inject_lambda_context(log_event=True)
    def handler(event, context):
        logger.info("Processing event")

    handler(test_event, durable_context)

    # THEN both the event and lambda contextual info should be logged
    logs = capture_multiple_logging_statements_output(stdout)
    assert len(logs) >= 2  # At least event log and info log

    # First log should be the event
    assert logs[0]["message"] == test_event


def test_inject_lambda_context_with_durable_context_clear_state(durable_context, stdout, service_name):
    """Test that inject_lambda_context with clear_state works with DurableContext."""
    # GIVEN Logger is initialized with custom keys
    logger = Logger(service=service_name, stream=stdout)
    logger.append_keys(custom_key="initial_value")

    # WHEN a lambda function is decorated with clear_state=True and receives DurableContext
    @logger.inject_lambda_context(clear_state=True)
    def handler(event, context):
        logger.info("After clear state")

    handler({}, durable_context)

    # THEN the custom key should be cleared and lambda context should be present
    log = capture_logging_output(stdout)

    # Lambda context fields should be present
    assert "function_name" in log
    assert log["function_name"] == durable_context.lambda_context.function_name

    # Custom key should not be present (cleared)
    assert "custom_key" not in log or log.get("custom_key") != "initial_value"


def test_inject_lambda_context_standard_context_still_works(lambda_context, stdout, service_name):
    """Test that standard Lambda context still works (regression test)."""
    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

    # WHEN a lambda function is decorated with logger and receives standard LambdaContext
    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Hello from standard lambda")

    handler({}, lambda_context)

    # THEN lambda contextual info should be in the logs
    log = capture_logging_output(stdout)

    expected_logger_context_keys = (
        "function_name",
        "function_memory_size",
        "function_arn",
        "function_request_id",
    )
    for key in expected_logger_context_keys:
        assert key in log

    assert log["function_name"] == lambda_context.function_name
    assert log["message"] == "Hello from standard lambda"
