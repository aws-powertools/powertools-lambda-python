"""aws_lambda_logging tests."""

from __future__ import annotations

import datetime as dt
import io
import json
import logging
import random
import string
import sys
import time
import warnings
from collections import namedtuple

import pytest

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.buffer import LoggerBufferConfig
from aws_lambda_powertools.logging.utils import copy_config_to_registered_loggers
from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.warnings import PowertoolsUserWarning


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
def stdout():
    return io.StringIO()


@pytest.fixture
def service_name():
    chars = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(chars) for _ in range(15))


def capture_logging_output(stdout):
    return json.loads(stdout.getvalue().strip())


def capture_multiple_logging_statements_output(stdout):
    return [json.loads(line.strip()) for line in stdout.getvalue().split("\n") if line]


@pytest.mark.parametrize("log_level", ["DEBUG", "WARNING", "INFO"])
def test_logger_buffer_with_minimum_level_warning(log_level, stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a buffer and minimum log level set to WARNING
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240, buffer_at_verbosity="WARNING")
    logger = Logger(level=log_level, service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    msg = "This is a test"
    log_command = {
        "INFO": logger.info,
        "WARNING": logger.warning,
        "DEBUG": logger.debug,
    }

    # WHEN Logging a message using the specified log level
    log_message = log_command[log_level]
    log_message(msg)
    log_dict = stdout.getvalue()

    # THEN verify that the message is buffered and not immediately output
    assert log_dict == ""


def test_logger_buffer_is_never_buffered_with_exception(stdout, service_name):
    # GIVEN A logger configured with a buffer and default logging behavior
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240)
    logger = Logger(service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN An exception is raised and logged
    try:
        raise ValueError("something went wrong")
    except Exception:
        logger.exception("Received an exception")

    # THEN We expect the log record is not buffered
    log = capture_logging_output(stdout)
    assert "Received an exception" == log["message"]


def test_logger_buffer_is_never_buffered_with_error(stdout, service_name):
    # GIVEN A logger configured with a buffer and default logging behavior
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240)
    logger = Logger(service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Logging an error message
    logger.error("Received an exception")

    # THEN The error log should be immediately output without buffering
    log = capture_logging_output(stdout)
    assert "Received an exception" == log["message"]


@pytest.mark.parametrize("log_level", ["CRITICAL", "ERROR"])
def test_logger_buffer_is_flushed_when_an_error_happens(stdout, service_name, log_level, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with buffer and automatic error-based flushing
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240, buffer_at_verbosity="DEBUG", flush_on_error_log=True)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Adding debug log messages before triggering an error
    logger.debug("this log line will be flushed")
    logger.debug("this log line will be flushed too")

    log_command = {
        "CRITICAL": logger.critical,
        "ERROR": logger.error,
        "EXCEPTION": logger.exception,
    }

    # WHEN Logging an error message using the specified log level
    log_message = log_command[log_level]
    log_message("Received an exception")

    # THEN: All buffered log messages should be flushed and output
    log = capture_multiple_logging_statements_output(stdout)
    assert isinstance(log, list)
    assert "this log line will be flushed" == log[0]["message"]
    assert "this log line will be flushed too" == log[1]["message"]


@pytest.mark.parametrize("log_level", ["CRITICAL", "ERROR"])
def test_logger_buffer_is_not_flushed_when_an_error_happens(stdout, service_name, log_level, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a buffer and error flushing disabled
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240, buffer_at_verbosity="DEBUG", flush_on_error_log=False)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Adding debug log messages before an error
    logger.debug("this log line will be flushed")
    logger.debug("this log line will be flushed too")

    log_command = {
        "CRITICAL": logger.critical,
        "ERROR": logger.error,
        "EXCEPTION": logger.exception,
    }

    # WHEN Logging an error message using the specified log level
    log_message = log_command[log_level]
    log_message("Received an exception")

    # THEN The error log message should be output, but previous debug logs should remain buffered
    log = capture_logging_output(stdout)
    assert not isinstance(log, list)
    assert "Received an exception" == log["message"]
    assert log_level == log["level"]


def test_create_and_flush_logs(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a large buffer
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Logging a message and then flushing the buffer
    logger.debug("this log line will be flushed")
    logger.flush_buffer()

    # THEN The log record should be immediately output and not remain buffered
    log = capture_multiple_logging_statements_output(stdout)
    assert "this log line will be flushed" == log[0]["message"]


def test_ensure_log_location_after_flush_buffer(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a sufficiently large buffer
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Logging a debug message and immediately flushing the buffer
    logger.debug("this log line will be flushed")
    logger.flush_buffer()

    # THEN Validate that the log location is precisely captured
    log = capture_multiple_logging_statements_output(stdout)
    assert "test_ensure_log_location_after_flush_buffer" in log[0]["location"]


def test_clear_buffer_during_execution(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a sufficiently large buffer
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN we clear the buffer during the execution
    logger.debug("this log line will be flushed")
    logger.clear_buffer()

    # THEN not log is flushed
    logger.flush_buffer()
    log = capture_multiple_logging_statements_output(stdout)
    assert not log


def test_exception_logging_during_buffer_flush(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a sufficiently large buffer
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # Custom exception class
    class MyError(Exception):
        pass

    # WHEN Logging an exception and flushing the buffer
    try:
        raise MyError("Test exception message")
    except MyError as error:
        logger.debug("Logging a test exception to verify buffer and exception handling", exc_info=error)

    logger.flush_buffer()

    # THEN Validate that the log exception fields
    log = capture_multiple_logging_statements_output(stdout)
    assert log[0]["exception_name"] == "MyError"
    assert "Test exception message" in log[0]["exception"]
    assert "test_exception_logging_during_buffer_flush" in log[0]["exception"]


def test_create_buffer_with_items_evicted(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a 1024-byte buffer
    logger_buffer_config = LoggerBufferConfig(max_bytes=1024, buffer_at_verbosity="DEBUG")
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Adding multiple log entries that exceed buffer size
    logger.debug("this log line will be flushed")
    logger.debug("this log line will be flushed")
    logger.debug("this log line will be flushed")
    logger.debug("this log line will be flushed")
    logger.debug("this log line will be flushed")

    # THEN A warning should be raised when flushing logs that exceed buffer capacity
    with pytest.warns(PowertoolsUserWarning, match="Some logs are not displayed because*"):
        logger.flush_buffer()


def test_create_buffer_with_items_evicted_with_next_invocation(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a 1024-byte buffer
    logger_buffer_config = LoggerBufferConfig(max_bytes=1024, buffer_at_verbosity="DEBUG")
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Adding multiple log entries that exceed buffer size
    message = "this log line will be flushed"
    logger.debug(message)
    logger.debug(message)
    logger.debug(message)
    logger.debug(message)
    logger.debug(message)

    # THEN First buffer flush triggers warning about log eviction
    with pytest.warns(PowertoolsUserWarning, match="Some logs are not displayed because*"):
        logger.flush_buffer()

    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "12345")
    # WHEN Adding another log entry after initial flush
    logger.debug("new log entry after buffer flush")

    # THEN Subsequent buffer flush should not trigger warning
    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")
        logger.flush_buffer()
        assert len(warning_list) == 0, "No warnings should be raised"


def test_flush_buffer_when_empty(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN: A logger configured with a 1024-byte buffer
    logger_buffer_config = LoggerBufferConfig(max_bytes=1024, buffer_at_verbosity="DEBUG")

    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN: Flushing the buffer without adding any log entries
    logger.flush_buffer()

    # THEN: No output should be generated
    log = capture_multiple_logging_statements_output(stdout)
    assert not log


def test_log_record_exceeding_buffer_size(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    message = "this log is bigger than entire buffer size"

    # GIVEN A logger configured with a small 10-byte buffer
    logger_buffer_config = LoggerBufferConfig(max_bytes=10, buffer_at_verbosity="DEBUG")

    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Attempting to log a message larger than the entire buffer
    # THEN A warning should be raised indicating buffer size limitation
    with pytest.warns(PowertoolsUserWarning, match="Cannot add item to the buffer*"):
        logger.debug(message)

    # THEN the log must be flushed to avoid data loss
    log = capture_multiple_logging_statements_output(stdout)
    assert log[0]["message"] == message


def test_log_record_exceeding_buffer_size_in_bytes(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN a message that fits the buffer in characters but not in UTF-8 bytes
    message = "é" * 1000

    # GIVEN A logger configured with a 1600-byte buffer
    logger_buffer_config = LoggerBufferConfig(max_bytes=1600, buffer_at_verbosity="DEBUG")

    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Logging the message
    # THEN A warning should be raised because the record is larger than max_bytes in bytes
    with pytest.warns(PowertoolsUserWarning, match="Cannot add item to the buffer*"):
        logger.debug(message)

    # THEN the log must be flushed to avoid data loss
    log = capture_multiple_logging_statements_output(stdout)
    assert log[0]["message"] == message


@pytest.mark.parametrize("log_level", ["WARNING", "INFO"])
def test_logger_buffer_log_output_for_levels_above_minimum(log_level, stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a buffer and minimum log level set to DEBUG
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240, buffer_at_verbosity="DEBUG")
    logger = Logger(level=log_level, service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    msg = f"This is a test with level {log_level}"
    log_command = {
        "INFO": logger.info,
        "WARNING": logger.warning,
    }

    # WHEN Logging a message using the specified log level higher than debug
    log_message = log_command[log_level]
    log_message(msg)

    # THEN: The logged message should be immediately output and not buffered
    log = capture_multiple_logging_statements_output(stdout)
    assert len(log) == 1
    assert log[0]["message"] == msg


def test_logger_buffer_flush_on_uncaught_exception(stdout, service_name, monkeypatch, lambda_context):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN: A logger configured with a large buffer and error-based flushing
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240, buffer_at_verbosity="DEBUG")
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    @logger.inject_lambda_context(flush_buffer_on_uncaught_error=True)
    def handler(event, context):
        # Log messages that should be flushed when an exception occurs
        logger.debug("this log line will be flushed after error - 1")
        logger.debug("this log line will be flushed after error - 2")
        raise ValueError("Test error")

    # WHEN Invoking the handler and expecting a ValueError
    with pytest.raises(ValueError):
        handler({}, lambda_context)

    # THEN Verify that buffered log messages are flushed before the exception
    log = capture_multiple_logging_statements_output(stdout)
    assert len(log) == 2, "Expected two log messages to be flushed"
    assert log[0]["message"] == "this log line will be flushed after error - 1"
    assert log[1]["message"] == "this log line will be flushed after error - 2"


def test_logger_buffer_not_flush_on_uncaught_exception(stdout, service_name, monkeypatch, lambda_context):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN: A logger configured with a large buffer and error-based flushing
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240, buffer_at_verbosity="DEBUG")
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    @logger.inject_lambda_context(flush_buffer_on_uncaught_error=False)
    def handler(event, context):
        # Log messages that should be flushed when an exception occurs
        logger.debug("this log line will be flushed after error - 1")
        logger.debug("this log line will be flushed after error - 2")
        raise ValueError("Test error")

    # WHEN Invoking the handler and expecting a ValueError
    with pytest.raises(ValueError):
        handler({}, lambda_context)

    # THEN Verify that buffered log messages are flushed before the exception
    log = capture_multiple_logging_statements_output(stdout)
    assert len(log) == 0


def test_flush_buffer_log_output_without_buffer_config(stdout, service_name, lambda_context, monkeypatch):
    # Set initial trace ID for first Lambda invocation
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger without buffer configuration
    logger = Logger(level="DEBUG", service=service_name, stream=stdout)

    @logger.inject_lambda_context(flush_buffer_on_uncaught_error=True)
    def handler(event, context):
        # Log messages are not buffered and should be output immediately
        logger.debug("debug message - 1")
        logger.debug("debug message - 2")
        raise ValueError("Test error")

    # WHEN Invoking the handler and expecting a ValueError
    # AND flush_buffer_on_uncaught_error is True but there is no logger buffer configuration
    with pytest.raises(ValueError):
        handler({}, lambda_context)

    # THEN Verify that log messages are flushed without any exception
    log = capture_multiple_logging_statements_output(stdout)
    assert len(log) == 2, "Expected two log messages"


def test_buffer_configuration_and_buffer_propagation_across_logger_instances(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with specific buffer settings
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240, buffer_at_verbosity="DEBUG")

    # Create primary logger with explicit buffer configuration
    primary_logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # Create secondary logger for the same service (should inherit buffer config)
    secondary_logger = Logger(level="DEBUG", service=service_name)

    # WHEN Logging messages and flushing the buffer
    primary_logger.debug("Log message from primary logger")
    secondary_logger.debug("Log message from secondary logger")
    primary_logger.flush_buffer()

    # THEN Verify log messages are correctly captured and output
    log = capture_multiple_logging_statements_output(stdout)

    assert "Log message from primary logger" == log[0]["message"]
    assert "Log message from secondary logger" == log[1]["message"]
    assert primary_logger._logger.powertools_buffer_config == secondary_logger._logger.powertools_buffer_config


def test_buffer_config_isolation_between_loggers_with_different_services(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with specific buffer settings
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240, buffer_at_verbosity="DEBUG")

    # Create primary logger with explicit buffer configuration
    buffered_logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # Configure another logger with a different service name
    unbuffered_logger = Logger(level="DEBUG", service="powertoolsxyz")

    # WHEN
    # Log messages using both loggers and flush the buffer
    buffered_logger.debug("Log message from buffered logger")
    unbuffered_logger.debug("Log message from unbuffered logger")
    buffered_logger.flush_buffer()

    # THEN The buffered logger's message is present in the output
    # THEN The loggers have different buffer configurations
    log = capture_multiple_logging_statements_output(stdout)

    assert "Log message from buffered logger" == log[0]["message"]
    assert len(log) == 1
    assert buffered_logger._logger.powertools_buffer_config != unbuffered_logger._logger.powertools_buffer_config


def test_buffer_configuration_propagation_across_child_logger_instances(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with specific buffer settings
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240, buffer_at_verbosity="DEBUG")

    # Create primary logger with explicit buffer configuration
    primary_logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # Create a child log
    secondary_logger = Logger(level="DEBUG", service=service_name, child=True)

    # WHEN Logging messages and flushing the buffer
    primary_logger.debug("Log message from primary logger")
    secondary_logger.debug("Log message from secondary logger")

    primary_logger.flush_buffer()

    # THEN Verify log messages are correctly captured and output only for primary logger
    # 1. Only one log message is output (from parent logger)
    # 2. Buffer configuration is shared between parent and child
    # 3. Buffer caches remain separate between instances
    log = capture_multiple_logging_statements_output(stdout)
    assert len(log) == 1
    assert primary_logger._buffer_config == secondary_logger._buffer_config
    assert primary_logger._buffer_cache != secondary_logger._buffer_cache


def test_logger_buffer_is_cleared_between_lambda_invocations_with_decorator(
    stdout,
    service_name,
    monkeypatch,
    lambda_context,
):
    # Set initial trace ID for first Lambda invocation
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with specific buffer parameters
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    @logger.inject_lambda_context
    def handler(event, context):
        logger.debug("debug line")

    # WHEN First Lambda invocation with initial trace ID
    handler({}, lambda_context)

    # WHEN New Lambda invocation arrives with different trace ID
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "2-ABC39786-5908a82a246fb67f3089263f")
    handler({}, lambda_context)

    # THEN Verify buffer for the original trace ID is cleared
    assert not logger._buffer_cache.get("1-67c39786-5908a82a246fb67f3089263f")


def test_logger_buffer_is_cleared_between_lambda_invocations_without_decoration(
    stdout,
    service_name,
    monkeypatch,
    lambda_context,
):
    # Set initial trace ID for first Lambda invocation
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with specific buffer parameters
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    def handler(event, context):
        logger.debug("debug line")

    # WHEN First Lambda invocation with initial trace ID
    handler({}, lambda_context)

    # WHEN New Lambda invocation arrives with different trace ID
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "2-ABC39786-5908a82a246fb67f3089263f")
    handler({}, lambda_context)

    # THEN Verify buffer for the original trace ID is cleared
    assert not logger._buffer_cache.get("1-67c39786-5908a82a246fb67f3089263f")


def test_warning_when_alc_less_verbose_than_buffer(stdout, monkeypatch):
    # GIVEN Lambda ALC set to INFO
    monkeypatch.setenv("AWS_LAMBDA_LOG_LEVEL", "INFO")
    # Set initial trace ID for first Lambda invocation
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # WHEN creating a logger with DEBUG buffer level
    # THEN a warning should be emitted
    with pytest.warns(PowertoolsUserWarning, match="Advanced Logging Controls*"):
        logger = Logger(service="test", level="DEBUG", buffer_config=LoggerBufferConfig(buffer_at_verbosity="DEBUG"))

    # AND logging a debug message
    logger.debug("This is a debug")

    # AND flushing buffer
    # THEN another warning should be emitted about ALC and buffer level mismatch
    with pytest.warns(PowertoolsUserWarning, match="Advanced Logging Controls*"):
        logger.flush_buffer()


def test_flush_buffer_preserves_percent_style_formatting(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a buffer
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Logging a message with percent-style formatting
    logger.debug("user=%s count=%d", "alice", 42)
    logger.flush_buffer()

    # THEN The flushed log should contain the interpolated message
    log = capture_multiple_logging_statements_output(stdout)
    assert log[0]["message"] == "user=alice count=42"


def test_logger_log_method_buffers_and_flushes_on_error(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with buffer and flush on error
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240, flush_on_error_log=True)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Logging debug via log() method
    logger.log(logging.DEBUG, "buffered via log()")

    # THEN Message should be buffered, not immediately output
    log = capture_multiple_logging_statements_output(stdout)
    assert not log

    # WHEN Logging error via log() method
    logger.log(logging.ERROR, "error via log()")

    # THEN Both the buffered debug log and error log should be output
    log = capture_multiple_logging_statements_output(stdout)
    assert len(log) == 2
    assert log[0]["message"] == "buffered via log()"
    assert log[1]["message"] == "error via log()"


def test_logger_warn_and_fatal_aliases(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with buffer and flush on error
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240, buffer_at_verbosity="WARNING", flush_on_error_log=True)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Logging via warn() alias
    logger.warn("buffered via warn()")

    # THEN Message should be buffered
    log = capture_multiple_logging_statements_output(stdout)
    assert not log

    # WHEN Logging via fatal() alias
    logger.fatal("flushed via fatal()")

    # THEN Buffer should flush and both messages should appear
    log = capture_multiple_logging_statements_output(stdout)
    assert len(log) == 2
    assert log[0]["message"] == "buffered via warn()"
    assert log[1]["message"] == "flushed via fatal()"


def test_logger_log_method_does_not_buffer_custom_level_above_threshold(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger that buffers DEBUG logs only
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240, buffer_at_verbosity="DEBUG")
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Logging with a custom level between INFO and WARNING
    logger.log(25, "custom level via log()")

    # THEN Message should be output right away, like info()
    log = capture_multiple_logging_statements_output(stdout)
    assert len(log) == 1
    assert log[0]["message"] == "custom level via log()"


def test_logger_log_method_supports_valid_string_level(stdout, service_name):
    # GIVEN A logger without buffering
    logger = Logger(level="DEBUG", service=service_name, stream=stdout)

    # WHEN Logging using string level name
    logger.log("INFO", "string level via log()")

    # THEN Message should be logged with INFO level
    log = capture_multiple_logging_statements_output(stdout)
    assert len(log) == 1
    assert log[0]["message"] == "string level via log()"
    assert log[0]["level"] == "INFO"


def test_logger_log_method_raises_on_invalid_level(stdout, service_name):
    # GIVEN A standard logger
    logger = Logger(level="DEBUG", service=service_name, stream=stdout)

    # WHEN Logging with an unknown string level
    # THEN ValueError should be raised
    with pytest.raises(ValueError, match="Unknown level: 'UNKNOWN_LEVEL'"):
        logger.log("UNKNOWN_LEVEL", "test message")

    # WHEN Logging with a non-int, non-string level (e.g. None)
    # THEN ValueError should be raised
    with pytest.raises(ValueError, match="Unknown level: None"):
        logger.log(None, "test message")  # type: ignore[arg-type]


def test_buffer_honours_stacklevel_when_flushed(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a buffer
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    def business():
        def wrapper():
            logger.debug("direct caller", stacklevel=2)
            logger.debug("caller of the wrapper", stacklevel=3)

        wrapper()

    # WHEN Logging from a nested function with different stacklevels and flushing the buffer
    business()
    logger.flush_buffer()

    # THEN Each flushed record reports the same location the unbuffered logger would
    logs = capture_multiple_logging_statements_output(stdout)
    assert "wrapper" in logs[0]["location"]
    assert "business" in logs[1]["location"]


def test_buffer_preserves_third_party_logger_name_location_and_stack_info(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a buffer, shared with a third-party logger
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)
    logger.append_keys(stack_info="%(stack_info)s")
    external_logger = logging.getLogger("external_library")
    external_logger.setLevel(logging.DEBUG)
    copy_config_to_registered_loggers(logger, include_buffering=True, include={external_logger.name})

    def library_function():
        external_logger.debug("from a third-party library", stack_info=True)

    # WHEN The third-party logger logs and the buffer is flushed
    library_function()
    logger.flush_buffer()

    # THEN The location and name are the library's, and the stack info is kept
    log = capture_logging_output(stdout)
    assert "library_function" in log["location"]
    assert log["name"] == "external_library"
    assert "Stack (most recent call last)" in log["stack_info"]


def test_buffer_preserves_provided_exc_info(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a buffer
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN An exception is saved outside its except block and logged later
    try:
        raise ValueError("saved")
    except ValueError:
        saved_exc_info = sys.exc_info()

    logger.debug("later", exc_info=saved_exc_info)
    logger.flush_buffer()

    # THEN The flushed record still carries the exception
    log = capture_logging_output(stdout)
    assert "ValueError: saved" in log["exception"]
    assert log["exception_name"] == "ValueError"


def test_buffer_preserves_original_timestamp(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")

    # GIVEN A logger configured with a buffer
    logger_buffer_config = LoggerBufferConfig(max_bytes=10240)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, buffer_config=logger_buffer_config)

    # WHEN Logging a message, waiting, and then flushing the buffer
    before = dt.datetime.now(dt.timezone.utc)
    logger.debug("this log line will be flushed")
    after = dt.datetime.now(dt.timezone.utc)
    time.sleep(0.4)
    logger.flush_buffer()

    # THEN The timestamp carries the creation milliseconds, not the flush time
    log = capture_logging_output(stdout)
    logged_at = dt.datetime.strptime(log["timestamp"], "%Y-%m-%d %H:%M:%S,%f%z")
    assert int(before.timestamp() * 1000) - 1 <= int(logged_at.timestamp() * 1000) <= int(after.timestamp() * 1000)


def test_logger_buffer_logs_immediately_without_trace_id(stdout, service_name, monkeypatch):
    monkeypatch.delenv(constants.XRAY_TRACE_ID_ENV, raising=False)

    logger_buffer_config = LoggerBufferConfig(
        max_bytes=10240,
        buffer_at_verbosity="DEBUG",
    )
    logger = Logger(
        level="DEBUG",
        service=service_name,
        stream=stdout,
        buffer_config=logger_buffer_config,
    )

    logger.debug("This message should be logged immediately")

    log = capture_multiple_logging_statements_output(stdout)

    assert len(log) == 1
    assert log[0]["message"] == "This message should be logged immediately"

    # Simulate the trace ID becoming available when the Lambda invocation starts
    monkeypatch.setenv(
        constants.XRAY_TRACE_ID_ENV,
        "1-67c39786-5908a82a246fb67f3089263f",
    )

    logger.flush_buffer()

    assert len(capture_multiple_logging_statements_output(stdout)) == 1
