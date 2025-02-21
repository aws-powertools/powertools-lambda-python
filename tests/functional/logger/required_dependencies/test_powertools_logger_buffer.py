"""aws_lambda_logging tests."""

import io
import json
import random
import string
import warnings
from collections import namedtuple

import pytest

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.buffer import LoggerBufferConfig
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
def test_logger_buffer_with_minimum_level_warning(log_level, stdout, service_name):
    # GIVEN a configured logger with buffer enabled and specific minimum log level
    logger_buffer_config = LoggerBufferConfig(max_size=10240, minimum_log_level="WARNING")
    logger = Logger(level=log_level, service=service_name, stream=stdout, logger_buffer=logger_buffer_config)

    msg = "This is a test"
    log_command = {
        "INFO": logger.info,
        "WARNING": logger.warning,
        "DEBUG": logger.debug,
    }

    # WHEN a log message is sent using the corresponding log method
    log_message = log_command[log_level]
    log_message(msg)
    log_dict = stdout.getvalue()

    # THEN verify that the message is buffered and not immediately output
    assert log_dict == ""


def test_logger_buffer_is_never_buffered_with_exception(stdout, service_name):
    # GIVEN: A logger configured with buffer
    logger_buffer_config = LoggerBufferConfig(max_size=10240)
    logger = Logger(service=service_name, stream=stdout, logger_buffer=logger_buffer_config)

    # WHEN: An exception is raised and logged
    try:
        raise ValueError("something went wrong")
    except Exception:
        logger.exception("Received an exception")

    # THEN: We expect the log record is not buffered
    log = capture_logging_output(stdout)
    assert "Received an exception" == log["message"]


def test_logger_buffer_is_never_buffered_with_error(stdout, service_name):
    # GIVEN: A logger configured with buffer
    logger_buffer_config = LoggerBufferConfig(max_size=10240)
    logger = Logger(service=service_name, stream=stdout, logger_buffer=logger_buffer_config)

    # WHEN: An exception is raised and logged
    logger.error("Received an exception")

    # THEN: We expect the log record is not buffered
    log = capture_logging_output(stdout)
    assert "Received an exception" == log["message"]


@pytest.mark.parametrize("log_level", ["CRITICAL", "ERROR"])
def test_logger_buffer_is_flushed_when_an_error_happens(stdout, service_name, log_level, monkeypatch):
    # GIVEN: A logger configured with buffer
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1234")
    logger_buffer_config = LoggerBufferConfig(max_size=10240, minimum_log_level="DEBUG", flush_on_error=True)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, logger_buffer=logger_buffer_config)

    logger.debug("this log line will be flushed")
    logger.debug("this log line will be flushed too")

    log_command = {
        "CRITICAL": logger.critical,
        "ERROR": logger.error,
        "EXCEPTION": logger.exception,
    }

    # WHEN a log message is sent using the corresponding log method
    log_message = log_command[log_level]
    log_message("Received an exception")

    # THEN: We expect the log record is not buffered
    log = capture_multiple_logging_statements_output(stdout)
    assert "this log line will be flushed" == log[0]["message"]
    assert "this log line will be flushed too" == log[1]["message"]


@pytest.mark.parametrize("log_level", ["CRITICAL", "ERROR"])
def test_logger_buffer_is_not_flushed_when_an_error_happens(stdout, service_name, log_level):
    # GIVEN: A logger configured with buffer
    logger_buffer_config = LoggerBufferConfig(max_size=10240, minimum_log_level="DEBUG", flush_on_error=False)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, logger_buffer=logger_buffer_config)

    logger.debug("this log line will be flushed")
    logger.debug("this log line will be flushed too")

    log_command = {
        "CRITICAL": logger.critical,
        "ERROR": logger.error,
        "EXCEPTION": logger.exception,
    }

    # WHEN a log message is sent using the corresponding log method
    log_message = log_command[log_level]
    log_message("Received an exception")

    # THEN: We expect the log record is not buffered
    log = capture_logging_output(stdout)
    assert "Received an exception" == log["message"]


def test_create_and_flush_logs(stdout, service_name, monkeypatch):
    # GIVEN: A logger configured with buffer
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1234")
    logger_buffer_config = LoggerBufferConfig(max_size=10240, minimum_log_level="DEBUG", flush_on_error=True)
    logger = Logger(level="DEBUG", service=service_name, stream=stdout, logger_buffer=logger_buffer_config)

    logger.debug("this log line will be flushed")

    logger.flush_buffer()

    # THEN: We expect the log record is not buffered
    log = capture_multiple_logging_statements_output(stdout)
    assert "this log line will be flushed" == log[0]["message"]


def test_create_buffer_with_item_overflow(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1234")

    # GIVEN: A logger configured with 2 bytes
    logger_buffer_config = LoggerBufferConfig(max_size=2, minimum_log_level="DEBUG")

    logger = Logger(level="DEBUG", service=service_name, stream=stdout, logger_buffer=logger_buffer_config)

    # WHEN logging a line with a size higher than buffer
    # THEN must raise a warning
    with pytest.warns(PowertoolsUserWarning, match="Item size*"):
        logger.debug("this log line will be flushed")


def test_create_buffer_with_items_evicted(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1234")

    # GIVEN: A logger configured with 1024 bytes
    logger_buffer_config = LoggerBufferConfig(max_size=1024, minimum_log_level="DEBUG")

    logger = Logger(level="DEBUG", service=service_name, stream=stdout, logger_buffer=logger_buffer_config)

    # WHEN we add 3 lines that exceeds than 1024 bytes
    logger.debug("this log line will be flushed")
    logger.debug("this log line will be flushed")
    logger.debug("this log line will be flushed")
    logger.debug("this log line will be flushed")
    logger.debug("this log line will be flushed")

    # THEN must raise a warning when trying to flush the lugs
    with pytest.warns(PowertoolsUserWarning, match="Some logs are not displayed because*"):
        logger.flush_buffer()


def test_create_buffer_with_items_evicted_next_invocation(stdout, service_name, monkeypatch):
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1234")

    # GIVEN: A logger configured with 1024 bytes
    logger_buffer_config = LoggerBufferConfig(max_size=1024, minimum_log_level="DEBUG")

    logger = Logger(level="DEBUG", service=service_name, stream=stdout, logger_buffer=logger_buffer_config)

    # WHEN Add multiple log entries that exceed buffer size
    message = "this log line will be flushed"
    logger.debug(message)
    logger.debug(message)
    logger.debug(message)
    logger.debug(message)
    logger.debug(message)

    # THEN First buffer flush triggers warning about log eviction
    with pytest.warns(PowertoolsUserWarning, match="Some logs are not displayed because*"):
        logger.flush_buffer()

    # WHEN Add another log entry
    logger.debug("new log entry after buffer flush")

    # THEN Subsequent buffer flush should not trigger warning
    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")
        logger.flush_buffer()
        assert len(warning_list) == 0, "No warnings should be raised"
