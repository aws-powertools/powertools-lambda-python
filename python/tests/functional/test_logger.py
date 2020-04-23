import io
import json
import logging
from collections import namedtuple

import pytest

from aws_lambda_powertools.logging import Logger, MetricUnit, log_metric, logger_inject_lambda_context, logger_setup


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


def test_setup_service_name(root_logger, stdout):
    # GIVEN service is explicitly defined
    # WHEN logger is setup
    # THEN service field should be equals service given
    service_name = "payment"
    logger = Logger(service=service_name, stream=stdout)

    logger.info("Hello")
    log = json.loads(stdout.getvalue())

    assert service_name == log["service"]


def test_setup_no_service_name(stdout):
    # GIVEN no service is explicitly defined
    # WHEN logger is setup
    # THEN service field should be "service_undefined"
    logger = Logger(stream=stdout)
    logger.info("Hello")
    log = json.loads(stdout.getvalue())

    assert "service_undefined" == log["service"]


def test_setup_service_env_var(monkeypatch, stdout):
    # GIVEN service is explicitly defined via POWERTOOLS_SERVICE_NAME env
    # WHEN logger is setup
    # THEN service field should be equals POWERTOOLS_SERVICE_NAME value
    service_name = "payment"
    monkeypatch.setenv("POWERTOOLS_SERVICE_NAME", service_name)

    logger = Logger(stream=stdout)
    logger.info("Hello")
    log = json.loads(stdout.getvalue())

    assert service_name == log["service"]


def test_setup_sampling_rate(monkeypatch, stdout):
    # GIVEN samping rate is explicitly defined via POWERTOOLS_LOGGER_SAMPLE_RATE env
    # WHEN logger is setup
    # THEN sampling rate should be equals POWERTOOLS_LOGGER_SAMPLE_RATE value and should sample debug logs

    sampling_rate = "1"
    monkeypatch.setenv("POWERTOOLS_LOGGER_SAMPLE_RATE", sampling_rate)
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    logger = Logger(stream=stdout)
    logger.debug("I am being sampled")
    log = json.loads(stdout.getvalue())

    assert sampling_rate == log["sampling_rate"]
    assert "DEBUG" == log["level"]
    assert "I am being sampled" == log["message"]


def test_inject_lambda_context(lambda_context, stdout):
    # GIVEN a lambda function is decorated with logger
    # WHEN logger is setup
    # THEN lambda contextual info should always be in the logs
    logger_context_keys = (
        "function_name",
        "function_memory_size",
        "function_arn",
        "function_request_id",
    )

    logger = Logger(stream=stdout)

    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Hello")

    handler({}, lambda_context)

    log = json.loads(stdout.getvalue())

    for key in logger_context_keys:
        assert key in log


def test_inject_lambda_context_log_event_request(lambda_context, stdout):
    # GIVEN a lambda function is decorated with logger instructed to log event
    # WHEN logger is setup
    # THEN logger should log event received from Lambda
    lambda_event = {"greeting": "hello"}

    logger = Logger(stream=stdout)

    @logger.inject_lambda_context(log_event=True)
    # @logger.inject_lambda_context(log_event=True)
    def handler(event, context):
        logger.info("Hello")

    handler(lambda_event, lambda_context)

    # Given that our string buffer has many log statements separated by newline \n
    # We need to clean it before we can assert on
    logs = [json.loads(line.strip()) for line in stdout.getvalue().split("\n") if line]
    logged_event, _ = logs
    assert "greeting" in logged_event["message"]


def test_inject_lambda_context_log_event_request_env_var(monkeypatch, lambda_context, stdout):
    # GIVEN a lambda function is decorated with logger instructed to log event
    # via POWERTOOLS_LOGGER_LOG_EVENT env
    # WHEN logger is setup
    # THEN logger should log event received from Lambda
    lambda_event = {"greeting": "hello"}
    monkeypatch.setenv("POWERTOOLS_LOGGER_LOG_EVENT", "true")

    logger = Logger(stream=stdout)

    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Hello")

    handler(lambda_event, lambda_context)

    # Given that our string buffer has many log statements separated by newline \n
    # We need to clean it before we can assert on
    logs = [json.loads(line.strip()) for line in stdout.getvalue().split("\n") if line]

    event = {}
    for log in logs:
        if "greeting" in log["message"]:
            event = log["message"]

    assert event == lambda_event


def test_inject_lambda_context_log_no_request_by_default(monkeypatch, lambda_context, stdout):
    # GIVEN a lambda function is decorated with logger
    # WHEN logger is setup
    # THEN logger should not log event received by lambda handler
    lambda_event = {"greeting": "hello"}

    logger = Logger(stream=stdout)

    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Hello")

    handler(lambda_event, lambda_context)

    # Given that our string buffer has many log statements separated by newline \n
    # We need to clean it before we can assert on
    logs = [json.loads(line.strip()) for line in stdout.getvalue().split("\n") if line]

    event = {}
    for log in logs:
        if "greeting" in log["message"]:
            event = log["message"]

    assert event != lambda_event


def test_inject_lambda_cold_start(lambda_context, stdout):
    # GIVEN a lambda function is decorated with logger, and called twice
    # WHEN logger is setup
    # THEN cold_start key should only be true in the first call

    from aws_lambda_powertools.logging import logger

    # # As we run tests in parallel global cold_start value can be false
    # # here we reset to simulate the correct behaviour
    # # since Lambda will only import our logger lib once per concurrent execution
    logger.is_cold_start = True

    logger = Logger(stream=stdout)

    def custom_method():
        logger.info("Hello from method")

    @logger.inject_lambda_context
    def handler(event, context):
        custom_method()
        logger.info("Hello")

    handler({}, lambda_context)
    handler({}, lambda_context)

    # Given that our string buffer has many log statements separated by newline \n
    # We need to clean it before we can assert on
    logs = [json.loads(line.strip()) for line in stdout.getvalue().split("\n") if line]
    first_log, second_log, third_log, fourth_log = logs

    # First execution
    assert "true" == first_log["cold_start"]
    assert "true" == second_log["cold_start"]

    # Second execution
    assert "false" == third_log["cold_start"]
    assert "false" == fourth_log["cold_start"]


def test_log_metric(capsys):
    # GIVEN a service, unit and value have been provided
    # WHEN log_metric is called
    # THEN custom metric line should be match given values
    log_metric(
        service="payment", name="test_metric", unit=MetricUnit.Seconds, value=60, namespace="DemoApp",
    )
    expected = "MONITORING|60|Seconds|test_metric|DemoApp|service=payment\n"
    captured = capsys.readouterr()

    assert captured.out == expected


def test_log_metric_env_var(monkeypatch, capsys):
    # GIVEN a service, unit and value have been provided
    # WHEN log_metric is called
    # THEN custom metric line should be match given values
    service_name = "payment"
    monkeypatch.setenv("POWERTOOLS_SERVICE_NAME", service_name)

    log_metric(name="test_metric", unit=MetricUnit.Seconds, value=60, namespace="DemoApp")
    expected = "MONITORING|60|Seconds|test_metric|DemoApp|service=payment\n"
    captured = capsys.readouterr()

    assert captured.out == expected


def test_log_metric_multiple_dimensions(capsys):
    # GIVEN multiple optional dimensions are provided
    # WHEN log_metric is called
    # THEN dimensions should appear as dimenion=value
    log_metric(
        name="test_metric", unit=MetricUnit.Seconds, value=60, customer="abc", charge_id="123", namespace="DemoApp",
    )
    expected = "MONITORING|60|Seconds|test_metric|DemoApp|service=service_undefined,customer=abc,charge_id=123\n"
    captured = capsys.readouterr()

    assert captured.out == expected


@pytest.mark.parametrize(
    "invalid_input,expected",
    [
        ({"unit": "seconds"}, "MONITORING|0|Seconds|test_metric|DemoApp|service=service_undefined\n",),
        (
            {"unit": "Seconds", "customer": None, "charge_id": "123", "payment_status": ""},
            "MONITORING|0|Seconds|test_metric|DemoApp|service=service_undefined,charge_id=123\n",
        ),
    ],
    ids=["metric unit as string lower case", "empty dimension value"],
)
def test_log_metric_partially_correct_args(capsys, invalid_input, expected):
    # GIVEN invalid arguments are provided such as empty dimension values and metric units in strings
    # WHEN log_metric is called
    # THEN default values should be used such as "Count" as a unit, invalid dimensions not included
    # and no exception raised
    log_metric(name="test_metric", namespace="DemoApp", **invalid_input)
    captured = capsys.readouterr()

    assert captured.out == expected


@pytest.mark.parametrize(
    "invalid_input,expected",
    [({"unit": "Blah"}, ValueError), ({"unit": None}, ValueError), ({}, TypeError)],
    ids=["invalid metric unit as str", "unit as None", "missing required unit"],
)
def test_log_metric_invalid_unit(capsys, invalid_input, expected):
    # GIVEN invalid units are provided
    # WHEN log_metric is called
    # THEN ValueError exception should be raised

    with pytest.raises(expected):
        log_metric(name="test_metric", namespace="DemoApp", **invalid_input)


def test_logger_setup_deprecated():
    # Should be removed when GA
    with pytest.raises(DeprecationWarning):
        logger_setup()


def test_logger_inject_lambda_context_deprecated():
    # Should be removed when GA
    with pytest.raises(DeprecationWarning):
        logger_setup()


def test_logger_append_duplicated(stdout):
    logger = Logger(stream=stdout, request_id="value")
    logger.structure_logs(append=True, request_id="new_value")
    logger.info("log")
    log = json.loads(stdout.getvalue())
    assert "new_value" == log["request_id"]
