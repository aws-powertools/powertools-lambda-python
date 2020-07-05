import io
import json
import logging
from collections import namedtuple

import pytest

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.logging.exceptions import InvalidLoggerSamplingRateError
from aws_lambda_powertools.logging.logger import set_package_logger


@pytest.fixture
def stdout():
    return io.StringIO()


@pytest.fixture
def handler(stdout):
    return logging.StreamHandler(stdout)


@pytest.fixture
def root_logger(handler):
    logging.root.addHandler(handler)
    yield logging.root
    logging.root.removeHandler(handler)


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
def lambda_event():
    return {"greeting": "hello"}


def capture_logging_output(stdout):
    return json.loads(stdout.getvalue())


def capture_multiple_logging_statements_output(stdout):
    return [json.loads(line.strip()) for line in stdout.getvalue().split("\n") if line]


def test_setup_service_name(root_logger, stdout):
    service_name = "payment"
    # GIVEN Logger is initialized
    # WHEN service is explicitly defined
    logger = Logger(service=service_name, stream=stdout)

    logger.info("Hello")

    # THEN service field should be equals service given
    log = capture_logging_output(stdout)
    assert service_name == log["service"]


def test_setup_no_service_name(stdout):
    # GIVEN Logger is initialized
    # WHEN no service is explicitly defined
    logger = Logger(stream=stdout)

    logger.info("Hello")

    # THEN service field should be "service_undefined"
    log = capture_logging_output(stdout)
    assert "service_undefined" == log["service"]


def test_setup_service_env_var(monkeypatch, stdout):
    service_name = "payment"
    # GIVEN Logger is initialized
    # WHEN service is explicitly defined via POWERTOOLS_SERVICE_NAME env
    monkeypatch.setenv("POWERTOOLS_SERVICE_NAME", service_name)
    logger = Logger(stream=stdout)

    logger.info("Hello")

    # THEN service field should be equals POWERTOOLS_SERVICE_NAME value
    log = capture_logging_output(stdout)
    assert service_name == log["service"]


def test_setup_sampling_rate_env_var(monkeypatch, stdout):
    # GIVEN Logger is initialized
    # WHEN samping rate is explicitly set to 100% via POWERTOOLS_LOGGER_SAMPLE_RATE env
    sampling_rate = "1"
    monkeypatch.setenv("POWERTOOLS_LOGGER_SAMPLE_RATE", sampling_rate)
    logger = Logger(stream=stdout, level="INFO")
    logger.debug("I am being sampled")

    # THEN sampling rate should be equals POWERTOOLS_LOGGER_SAMPLE_RATE value
    # log level should be DEBUG
    # and debug log statements should be in stdout
    log = capture_logging_output(stdout)
    assert sampling_rate == log["sampling_rate"]
    assert "DEBUG" == log["level"]
    assert "I am being sampled" == log["message"]


def test_inject_lambda_context(lambda_context, stdout):
    # GIVEN Logger is initialized
    logger = Logger(stream=stdout)

    # WHEN a lambda function is decorated with logger
    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Hello")

    handler({}, lambda_context)

    # THEN lambda contextual info should always be in the logs
    log = capture_logging_output(stdout)
    expected_logger_context_keys = (
        "function_name",
        "function_memory_size",
        "function_arn",
        "function_request_id",
    )
    for key in expected_logger_context_keys:
        assert key in log


def test_inject_lambda_context_log_event_request(lambda_context, stdout, lambda_event):
    # GIVEN Logger is initialized
    logger = Logger(stream=stdout)

    # WHEN a lambda function is decorated with logger instructed to log event
    @logger.inject_lambda_context(log_event=True)
    def handler(event, context):
        logger.info("Hello")

    handler(lambda_event, lambda_context)

    # THEN logger should log event received from Lambda
    logged_event, _ = capture_multiple_logging_statements_output(stdout)
    assert logged_event["message"] == lambda_event


def test_inject_lambda_context_log_event_request_env_var(monkeypatch, lambda_context, stdout, lambda_event):
    # GIVEN Logger is initialized
    monkeypatch.setenv("POWERTOOLS_LOGGER_LOG_EVENT", "true")
    logger = Logger(stream=stdout)

    # WHEN a lambda function is decorated with logger instructed to log event
    # via POWERTOOLS_LOGGER_LOG_EVENT env
    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Hello")

    handler(lambda_event, lambda_context)

    # THEN logger should log event received from Lambda
    logged_event, _ = capture_multiple_logging_statements_output(stdout)
    assert logged_event["message"] == lambda_event


def test_inject_lambda_context_log_no_request_by_default(monkeypatch, lambda_context, stdout, lambda_event):
    # GIVEN Logger is initialized
    logger = Logger(stream=stdout)

    # WHEN a lambda function is decorated with logger
    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Hello")

    handler(lambda_event, lambda_context)

    # THEN logger should not log event received by lambda handler
    log = capture_logging_output(stdout)
    assert log["message"] != lambda_event


def test_inject_lambda_cold_start(lambda_context, stdout):
    # cold_start can be false as it's a global variable in Logger module
    # so we reset it to simulate the correct behaviour
    # since Lambda will only import our logger lib once per concurrent execution
    from aws_lambda_powertools.logging import logger

    logger.is_cold_start = True

    # GIVEN Logger is initialized
    logger = Logger(stream=stdout)

    # WHEN a lambda function is decorated with logger, and called twice
    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Hello")

    handler({}, lambda_context)
    handler({}, lambda_context)

    # THEN cold_start key should only be true in the first call
    first_log, second_log = capture_multiple_logging_statements_output(stdout)
    assert first_log["cold_start"] is True
    assert second_log["cold_start"] is False


def test_package_logger_stream(stdout):
    # GIVEN package logger "aws_lambda_powertools" is explicitly set with no params
    set_package_logger(stream=stdout)

    # WHEN Tracer is initialized in disabled mode
    Tracer(disabled=True)

    # THEN Tracer debug log statement should be logged
    output = stdout.getvalue()
    logger = logging.getLogger("aws_lambda_powertools")
    assert "Tracing has been disabled" in output
    assert logger.level == logging.DEBUG


def test_package_logger_format(capsys):
    # GIVEN package logger "aws_lambda_powertools" is explicitly
    # with a custom formatter
    formatter = logging.Formatter("message=%(message)s")
    set_package_logger(formatter=formatter)

    # WHEN Tracer is initialized in disabled mode
    Tracer(disabled=True)

    # THEN Tracer debug log statement should be logged using `message=` format
    output = capsys.readouterr().out
    logger = logging.getLogger("aws_lambda_powertools")
    assert "message=" in output
    assert logger.level == logging.DEBUG


def test_logger_append_duplicated(stdout):
    # GIVEN Logger is initialized with request_id field
    logger = Logger(stream=stdout, request_id="value")

    # WHEN `request_id` is appended to the existing structured log
    # using a different value
    logger.structure_logs(append=True, request_id="new_value")
    logger.info("log")

    # THEN subsequent log statements should have the latest value
    log = capture_logging_output(stdout)
    assert "new_value" == log["request_id"]


def test_logger_invalid_sampling_rate():
    # GIVEN Logger is initialized
    # WHEN sampling_rate non-numeric value
    # THEN we should raise InvalidLoggerSamplingRateError
    with pytest.raises(InvalidLoggerSamplingRateError):
        Logger(sampling_rate="TEST")


def test_inject_lambda_context_with_structured_log(lambda_context, stdout):
    # GIVEN Logger is initialized
    logger = Logger(stream=stdout)

    # WHEN structure_logs has been used to add an additional key upfront
    # and a lambda function is decorated with logger.inject_lambda_context
    logger.structure_logs(append=True, additional_key="test")

    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Hello")

    handler({}, lambda_context)

    # THEN lambda contextual info should always be in the logs
    log = capture_logging_output(stdout)
    expected_logger_context_keys = (
        "function_name",
        "function_memory_size",
        "function_arn",
        "function_request_id",
        "additional_key",
    )
    for key in expected_logger_context_keys:
        assert key in log
