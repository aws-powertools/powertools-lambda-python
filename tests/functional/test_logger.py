import functools
import inspect
import io
import json
import logging
import random
import re
import string
import sys
import warnings
from ast import Dict
from collections import namedtuple
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, List, Optional, Union

import pytest

from aws_lambda_powertools import Logger, Tracer, set_package_logger_handler
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.logging.exceptions import InvalidLoggerSamplingRateError
from aws_lambda_powertools.logging.formatter import (
    BasePowertoolsFormatter,
    LambdaPowertoolsFormatter,
)
from aws_lambda_powertools.logging.logger import set_package_logger
from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.utilities.data_classes import S3Event, event_source


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
def lambda_event():
    return {"greeting": "hello"}


@pytest.fixture
def service_name():
    chars = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(chars) for _ in range(15))


def capture_logging_output(stdout):
    return json.loads(stdout.getvalue().strip())


def capture_multiple_logging_statements_output(stdout):
    return [json.loads(line.strip()) for line in stdout.getvalue().split("\n") if line]


def test_setup_service_name(stdout, service_name):
    # GIVEN Logger is initialized
    # WHEN service is explicitly defined
    logger = Logger(service=service_name, stream=stdout)

    logger.info("Hello")

    # THEN service field should be equals service given
    log = capture_logging_output(stdout)
    assert service_name == log["service"]


def test_setup_service_env_var(monkeypatch, stdout, service_name):
    # GIVEN Logger is initialized
    # WHEN service is explicitly defined via POWERTOOLS_SERVICE_NAME env
    monkeypatch.setenv("POWERTOOLS_SERVICE_NAME", service_name)
    logger = Logger(stream=stdout)

    logger.info("Hello")

    # THEN service field should be equals POWERTOOLS_SERVICE_NAME value
    log = capture_logging_output(stdout)
    assert service_name == log["service"]


def test_setup_sampling_rate_env_var(monkeypatch, stdout, service_name):
    # GIVEN Logger is initialized
    # WHEN samping rate is explicitly set to 100% via POWERTOOLS_LOGGER_SAMPLE_RATE env
    sampling_rate = "1"
    monkeypatch.setenv("POWERTOOLS_LOGGER_SAMPLE_RATE", sampling_rate)
    logger = Logger(service=service_name, stream=stdout)
    logger.debug("I am being sampled")

    # THEN sampling rate should be equals POWERTOOLS_LOGGER_SAMPLE_RATE value
    # log level should be DEBUG
    # and debug log statements should be in stdout
    log = capture_logging_output(stdout)
    assert sampling_rate == log["sampling_rate"]
    assert "DEBUG" == log["level"]
    assert "I am being sampled" == log["message"]


def test_inject_lambda_context(lambda_context, stdout, service_name):
    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

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


def test_inject_lambda_context_log_event_request(lambda_context, stdout, lambda_event, service_name):
    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

    # WHEN a lambda function is decorated with logger instructed to log event
    @logger.inject_lambda_context(log_event=True)
    def handler(event, context):
        logger.info("Hello")

    handler(lambda_event, lambda_context)

    # THEN logger should log event received from Lambda
    logged_event, _ = capture_multiple_logging_statements_output(stdout)
    assert logged_event["message"] == lambda_event


def test_inject_lambda_context_log_event_request_env_var(
    monkeypatch,
    lambda_context,
    stdout,
    lambda_event,
    service_name,
):
    # GIVEN Logger is initialized
    monkeypatch.setenv("POWERTOOLS_LOGGER_LOG_EVENT", "true")
    logger = Logger(service=service_name, stream=stdout)

    # WHEN a lambda function is decorated with logger instructed to log event
    # via POWERTOOLS_LOGGER_LOG_EVENT env
    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Hello")

    handler(lambda_event, lambda_context)

    # THEN logger should log event received from Lambda
    logged_event, _ = capture_multiple_logging_statements_output(stdout)
    assert logged_event["message"] == lambda_event


def test_inject_lambda_context_log_no_request_by_default(
    monkeypatch,
    lambda_context,
    stdout,
    lambda_event,
    service_name,
):
    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

    # WHEN a lambda function is decorated with logger
    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Hello")

    handler(lambda_event, lambda_context)

    # THEN logger should not log event received by lambda handler
    log = capture_logging_output(stdout)
    assert log["message"] != lambda_event


def test_inject_lambda_cold_start(lambda_context, stdout, service_name):
    # cold_start can be false as it's a global variable in Logger module
    # so we reset it to simulate the correct behaviour
    # since Lambda will only import our logger lib once per concurrent execution
    from aws_lambda_powertools.logging import logger

    logger.is_cold_start = True

    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

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


def test_logger_append_duplicated(stdout, service_name):
    # GIVEN Logger is initialized with request_id field
    logger = Logger(service=service_name, stream=stdout, request_id="value")

    # WHEN `request_id` is appended to the existing structured log
    # using a different value
    logger.structure_logs(append=True, request_id="new_value")
    logger.info("log")

    # THEN subsequent log statements should have the latest value
    log = capture_logging_output(stdout)
    assert "new_value" == log["request_id"]


def test_logger_honors_given_exception_keys(stdout, service_name):
    # GIVEN Logger is initialized with exception and exception_name fields
    logger = Logger(service=service_name, stream=stdout)

    # WHEN log level info
    logger.info("log", exception="exception_value", exception_name="exception_name_value")

    # THEN log statements should have these keys
    log = capture_logging_output(stdout)
    assert "exception_value" == log["exception"]
    assert "exception_name_value" == log["exception_name"]


def test_logger_invalid_sampling_rate(service_name):
    # GIVEN Logger is initialized
    # WHEN sampling_rate non-numeric value
    # THEN we should raise InvalidLoggerSamplingRateError
    with pytest.raises(InvalidLoggerSamplingRateError):
        Logger(service=service_name, stream=stdout, sampling_rate="TEST")


def test_inject_lambda_context_with_structured_log(lambda_context, stdout, service_name):
    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

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


def test_logger_children_propagate_changes(stdout, service_name):
    # GIVEN Loggers are initialized
    # create child logger before parent to mimick
    # importing logger from another module/file
    # as loggers are created in global scope
    child = Logger(stream=stdout, service=service_name, child=True)
    parent = Logger(stream=stdout, service=service_name)

    # WHEN a child Logger adds an additional key
    child.structure_logs(append=True, customer_id="value")

    # THEN child Logger changes should propagate to parent
    # and subsequent log statements should have the latest value
    parent.info("Hello parent")
    child.info("Hello child")

    parent_log, child_log = capture_multiple_logging_statements_output(stdout)
    assert "customer_id" in parent_log
    assert "customer_id" in child_log
    assert child.parent.name == service_name


def test_logger_child_not_set_returns_same_logger(stdout):
    # GIVEN two Loggers are initialized with the same service name
    # WHEN child param isn't set
    logger_one = Logger(service="something", stream=stdout)
    logger_two = Logger(service="something", stream=stdout)

    # THEN we should have two Logger instances
    # however inner logger wise should be the same
    assert id(logger_one) != id(logger_two)
    assert logger_one._logger is logger_two._logger
    assert logger_one.name is logger_two.name

    # THEN we should also not see any duplicated logs
    logger_one.info("One - Once")
    logger_two.info("Two - Once")

    logs = list(capture_multiple_logging_statements_output(stdout))
    assert len(logs) == 2


def test_logger_level_case_insensitive(service_name):
    # GIVEN a Loggers is initialized
    # WHEN log level is set as "info" instead of "INFO"
    logger = Logger(service=service_name, level="info")

    # THEN we should correctly set log level as INFO
    assert logger.level == logging.INFO


def test_logger_level_not_set(service_name):
    # GIVEN a Loggers is initialized
    # WHEN no log level was passed
    logger = Logger(service=service_name)

    # THEN we should default to INFO
    assert logger.level == logging.INFO


def test_logger_level_as_int(service_name):
    # GIVEN a Loggers is initialized
    # WHEN log level is int
    logger = Logger(service=service_name, level=logging.INFO)

    # THEN we should be expected int (20, in this case)
    assert logger.level == logging.INFO


def test_logger_level_env_var_as_int(monkeypatch, service_name):
    # GIVEN Logger is initialized
    # WHEN log level is explicitly defined via LOG_LEVEL env as int
    # THEN Logger should propagate ValueError
    # since env vars can only be string
    # and '50' is not a correct log level
    monkeypatch.setenv("LOG_LEVEL", 50)
    with pytest.raises(ValueError, match="Unknown level: '50'"):
        Logger(service=service_name)


def test_logger_switch_between_levels(stdout, service_name):
    # GIVEN a Loggers is initialized with INFO level
    logger = Logger(service=service_name, level="INFO", stream=stdout)
    logger.info("message info")

    # WHEN we switch to DEBUG level
    logger.setLevel(level="DEBUG")
    logger.debug("message debug")

    # THEN we must have different levels and messages in stdout
    log_output = capture_multiple_logging_statements_output(stdout)
    assert log_output[0]["level"] == "INFO"
    assert log_output[0]["message"] == "message info"
    assert log_output[1]["level"] == "DEBUG"
    assert log_output[1]["message"] == "message debug"


def test_logger_record_caller_location(stdout, service_name):
    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

    # WHEN log statement is run
    logger.info("log")

    # THEN 'location' field should have
    # the correct caller resolution
    caller_fn_name = inspect.currentframe().f_code.co_name
    log = capture_logging_output(stdout)
    assert caller_fn_name in log["location"]


def test_logger_do_not_log_twice_when_root_logger_is_setup(stdout, service_name):
    # GIVEN Lambda configures the root logger with a handler
    root_logger = logging.getLogger()
    root_logger.addHandler(logging.StreamHandler(stream=stdout))

    # WHEN we create a new Logger and child Logger
    logger = Logger(service=service_name, stream=stdout)
    child_logger = Logger(service=service_name, child=True, stream=stdout)
    logger.info("PARENT")
    child_logger.info("CHILD")
    root_logger.info("ROOT")

    # THEN it should only contain only two log entries
    # since child's log records propagated to root logger should be rejected
    logs = list(stdout.getvalue().strip().split("\n"))
    assert len(logs) == 2


def test_logger_extra_kwargs(stdout, service_name):
    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

    # WHEN `request_id` is an extra field in a log message to the existing structured log
    fields = {"request_id": "blah"}

    logger.info("with extra fields", extra=fields)
    logger.info("without extra fields")

    extra_fields_log, no_extra_fields_log = capture_multiple_logging_statements_output(stdout)

    # THEN first log should have request_id field in the root structure
    assert "request_id" in extra_fields_log

    # THEN second log should not have request_id in the root structure
    assert "request_id" not in no_extra_fields_log


def test_logger_arbitrary_fields_as_kwargs(stdout, service_name):
    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

    # WHEN `request_id` is an arbitrary field in a log message to the existing structured log
    fields = {"request_id": "blah"}

    logger.info("with arbitrary fields", **fields)
    logger.info("without extra fields")

    extra_fields_log, no_extra_fields_log = capture_multiple_logging_statements_output(stdout)

    # THEN first log should have request_id field in the root structure
    assert "request_id" in extra_fields_log

    # THEN second log should not have request_id in the root structure
    assert "request_id" not in no_extra_fields_log


def test_logger_log_twice_when_log_filter_isnt_present_and_root_logger_is_setup(monkeypatch, stdout, service_name):
    # GIVEN Lambda configures the root logger with a handler
    root_logger = logging.getLogger()
    root_logger.addHandler(logging.StreamHandler(stream=stdout))

    # WHEN we create a new Logger and child Logger
    # and log deduplication filter for child messages are disabled
    # see #262 for more details on why this is needed for Pytest Live Log feature
    monkeypatch.setenv(constants.LOGGER_LOG_DEDUPLICATION_ENV, "true")
    logger = Logger(service=service_name, stream=stdout)
    child_logger = Logger(service=service_name, child=True, stream=stdout)
    logger.info("PARENT")
    child_logger.info("CHILD")

    # THEN it should only contain only two log entries
    # since child's log records propagated to root logger should be rejected
    logs = list(stdout.getvalue().strip().split("\n"))
    assert len(logs) == 4


def test_logger_exception_extract_exception_name(stdout, service_name):
    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

    # WHEN calling a logger.exception with a ValueError
    try:
        raise ValueError("something went wrong")
    except Exception:
        logger.exception("Received an exception")

    # THEN we expect a "exception_name" to be "ValueError"
    log = capture_logging_output(stdout)
    assert "ValueError" == log["exception_name"]


def test_logger_set_correlation_id(lambda_context, stdout, service_name):
    # GIVEN
    logger = Logger(service=service_name, stream=stdout)
    request_id = "xxx-111-222"
    mock_event = {"requestContext": {"requestId": request_id}}

    def handler(event, _):
        logger.set_correlation_id(event["requestContext"]["requestId"])
        logger.info("Foo")

    # WHEN
    handler(mock_event, lambda_context)

    # THEN
    log = capture_logging_output(stdout)
    assert request_id == log["correlation_id"]


def test_logger_get_correlation_id(lambda_context, stdout, service_name):
    # GIVEN a logger with a correlation_id set
    logger = Logger(service=service_name, stream=stdout)
    logger.set_correlation_id("foo")

    # WHEN calling get_correlation_id
    correlation_id = logger.get_correlation_id()

    # THEN it should return the correlation_id
    assert "foo" == correlation_id


def test_logger_set_correlation_id_path(lambda_context, stdout, service_name):
    # GIVEN
    logger = Logger(service=service_name, stream=stdout)
    request_id = "xxx-111-222"
    mock_event = {"requestContext": {"requestId": request_id}}

    @logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
    def handler(event, context):
        logger.info("Foo")

    # WHEN
    handler(mock_event, lambda_context)

    # THEN
    log = capture_logging_output(stdout)
    assert request_id == log["correlation_id"]


def test_logger_append_remove_keys(stdout, service_name):
    # GIVEN a Logger is initialized
    logger = Logger(service=service_name, stream=stdout)
    extra_keys = {"request_id": "id", "context": "value"}

    # WHEN keys are updated
    logger.append_keys(**extra_keys)
    logger.info("message with new keys")

    # And removed
    logger.remove_keys(extra_keys.keys())
    logger.info("message after keys being removed")

    # THEN additional keys should only be present in the first log statement
    extra_keys_log, keys_removed_log = capture_multiple_logging_statements_output(stdout)

    assert extra_keys.items() <= extra_keys_log.items()
    assert (extra_keys.items() <= keys_removed_log.items()) is False


def test_logger_custom_formatter(stdout, service_name, lambda_context):
    class CustomFormatter(BasePowertoolsFormatter):
        custom_format = {}

        def append_keys(self, **additional_keys):
            self.custom_format.update(additional_keys)

        def remove_keys(self, keys: Iterable[str]):
            for key in keys:
                self.custom_format.pop(key, None)

        def clear_state(self):
            self.custom_format.clear()

        def format(self, record: logging.LogRecord) -> str:  # noqa: A003
            return json.dumps(
                {
                    "message": super().format(record),
                    "timestamp": self.formatTime(record),
                    "my_default_key": "test",
                    **self.custom_format,
                },
            )

    custom_formatter = CustomFormatter()

    # GIVEN a Logger is initialized with a custom formatter
    logger = Logger(service=service_name, stream=stdout, logger_formatter=custom_formatter)

    # WHEN a lambda function is decorated with logger
    @logger.inject_lambda_context(correlation_id_path="foo")
    def handler(event, context):
        logger.info("Hello")

    handler({"foo": "value"}, lambda_context)

    lambda_context_keys = (
        "function_name",
        "function_memory_size",
        "function_arn",
        "function_request_id",
    )

    log = capture_logging_output(stdout)

    # THEN custom key should always be present
    # and lambda contextual info should also be in the logs
    # and get_correlation_id should return None
    assert "my_default_key" in log
    assert all(k in log for k in lambda_context_keys)
    assert log["correlation_id"] == "value"
    assert logger.get_correlation_id() is None


def test_logger_custom_powertools_formatter_clear_state(stdout, service_name, lambda_context):
    class CustomFormatter(LambdaPowertoolsFormatter):
        def __init__(
            self,
            json_serializer: Optional[Callable[[Dict], str]] = None,
            json_deserializer: Optional[Callable[[Union[Dict, str, bool, int, float]], str]] = None,
            json_default: Optional[Callable[[Any], Any]] = None,
            datefmt: Optional[str] = None,
            use_datetime_directive: bool = False,
            log_record_order: Optional[List[str]] = None,
            utc: bool = False,
            **kwargs,
        ):
            super().__init__(
                json_serializer,
                json_deserializer,
                json_default,
                datefmt,
                use_datetime_directive,
                log_record_order,
                utc,
                **kwargs,
            )

    custom_formatter = CustomFormatter()

    # GIVEN a Logger is initialized with a custom formatter
    logger = Logger(service=service_name, stream=stdout, logger_formatter=custom_formatter)

    # WHEN a lambda function is decorated with logger
    # and state is to be cleared in the next invocation
    @logger.inject_lambda_context(clear_state=True)
    def handler(event, context):
        if event.get("add_key"):
            logger.append_keys(my_key="value")
        logger.info("Hello")

    handler({"add_key": True}, lambda_context)
    handler({}, lambda_context)

    lambda_context_keys = (
        "function_name",
        "function_memory_size",
        "function_arn",
        "function_request_id",
    )

    first_log, second_log = capture_multiple_logging_statements_output(stdout)

    # THEN my_key should only present once
    # and lambda contextual info should also be in both logs
    assert "my_key" in first_log
    assert "my_key" not in second_log
    assert all(k in first_log for k in lambda_context_keys)
    assert all(k in second_log for k in lambda_context_keys)


def test_logger_custom_formatter_has_standard_and_custom_keys(stdout, service_name, lambda_context):
    class CustomFormatter(LambdaPowertoolsFormatter):
        ...

    # GIVEN a Logger is initialized with a custom formatter
    logger = Logger(service=service_name, stream=stdout, logger_formatter=CustomFormatter(), my_key="value")

    # WHEN a lambda function is decorated with logger
    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("Hello")

    handler({}, lambda_context)

    standard_keys = (
        "level",
        "location",
        "message",
        "timestamp",
        "service",
        "cold_start",
        "function_name",
        "function_memory_size",
        "function_arn",
        "function_request_id",
    )

    log = capture_logging_output(stdout)

    # THEN all standard keys should be available
    assert all(k in log for k in standard_keys)
    assert "my_key" in log


def test_logger_custom_handler(lambda_context, service_name, tmp_path):
    # GIVEN a Logger is initialized with a FileHandler
    log_file = tmp_path / "log.json"
    handler = logging.FileHandler(filename=log_file)
    logger = Logger(service=service_name, logger_handler=handler)

    # WHEN a log statement happens
    @logger.inject_lambda_context
    def handler(event, context):
        logger.info("custom handler")

    handler({}, lambda_context)

    # THEN we should output to a file not stdout
    log = log_file.read_text()
    assert "custom handler" in log


def test_clear_state_on_inject_lambda_context(lambda_context, stdout, service_name):
    # GIVEN
    logger = Logger(service=service_name, stream=stdout)

    # WHEN clear_state is set and a key was conditionally added in the first invocation
    @logger.inject_lambda_context(clear_state=True)
    def handler(event, context):
        if event.get("add_key"):
            logger.append_keys(my_key="value")
        logger.info("Foo")

    # THEN custom key should only exist in the first log
    handler({"add_key": True}, lambda_context)
    handler({}, lambda_context)

    first_log, second_log = capture_multiple_logging_statements_output(stdout)
    assert "my_key" in first_log
    assert "my_key" not in second_log


def test_clear_state_keeps_standard_keys(lambda_context, stdout, service_name):
    # GIVEN
    logger = Logger(service=service_name, stream=stdout)
    standard_keys = ["level", "location", "message", "timestamp", "service"]

    # WHEN clear_state is set
    @logger.inject_lambda_context(clear_state=True)
    def handler(event, context):
        logger.info("Foo")

    # THEN all standard keys should be available as usual
    handler({}, lambda_context)
    handler({}, lambda_context)

    first_log, second_log = capture_multiple_logging_statements_output(stdout)
    for key in standard_keys:
        assert key in first_log
        assert key in second_log


def test_clear_state_keeps_custom_keys(lambda_context, stdout, service_name):
    # GIVEN
    location_format = "%(module)s.%(funcName)s:clear_state"
    logger = Logger(service=service_name, stream=stdout, location=location_format, custom_key="foo")

    # WHEN clear_state is set
    @logger.inject_lambda_context(clear_state=True)
    def handler(event, context):
        logger.info("Foo")

    # THEN all standard keys should be available as usual
    handler({}, lambda_context)
    handler({}, lambda_context)

    first_log, second_log = capture_multiple_logging_statements_output(stdout)
    for log in (first_log, second_log):
        assert "foo" == log["custom_key"]
        assert "test_logger.handler:clear_state" == log["location"]


def test_clear_state_keeps_exception_keys(lambda_context, stdout, service_name):
    # GIVEN
    logger = Logger(service=service_name, stream=stdout)

    # WHEN clear_state is set and an exception was logged
    @logger.inject_lambda_context(clear_state=True)
    def handler(event, context):
        try:
            raise ValueError("something went wrong")
        except Exception:
            logger.exception("Received an exception")

    # THEN we expect a "exception_name" to be "ValueError"
    handler({}, lambda_context)
    log = capture_logging_output(stdout)
    assert "ValueError" == log["exception_name"]


def test_inject_lambda_context_allows_handler_with_kwargs(lambda_context, stdout, service_name):
    # GIVEN
    logger = Logger(service=service_name, stream=stdout)

    # WHEN
    @logger.inject_lambda_context(clear_state=True)
    def handler(event, context, my_custom_option=None):
        pass

    # THEN
    handler({}, lambda_context, my_custom_option="blah")


@pytest.mark.parametrize("utc", [False, True])
def test_use_datetime(stdout, service_name, utc):
    # GIVEN
    logger = Logger(
        service=service_name,
        stream=stdout,
        datefmt="custom timestamp: milliseconds=%F microseconds=%f timezone=%z",
        use_datetime_directive=True,
        utc=utc,
    )

    # WHEN a log statement happens
    logger.info({})

    # THEN the timestamp has the appropriate formatting
    log = capture_logging_output(stdout)

    expected_tz = datetime.now().astimezone(timezone.utc if utc else None).strftime("%z")
    assert re.fullmatch(
        f"custom timestamp: milliseconds=[0-9]+ microseconds=[0-9]+ timezone={re.escape(expected_tz)}",
        log["timestamp"],
    )


@pytest.mark.parametrize("utc", [False, True])
def test_use_rfc3339_iso8601(stdout, service_name, utc):
    # GIVEN
    logger = Logger(service=service_name, stream=stdout, use_rfc3339=True, utc=utc)
    RFC3339_REGEX = r"^((?:(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2}(?:\.\d+)?))(Z|[\+-]\d{2}:\d{2})?)$"

    # WHEN a log statement happens
    logger.info({})

    # THEN the timestamp has the appropriate formatting
    log = capture_logging_output(stdout)

    assert re.fullmatch(RFC3339_REGEX, log["timestamp"])  # "2022-10-27T17:42:26.841+0200"


def test_inject_lambda_context_log_event_request_data_classes(lambda_context, stdout, lambda_event, service_name):
    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

    # WHEN a lambda function is decorated with logger instructed to log event
    # AND the event is an event source data class
    @event_source(data_class=S3Event)
    @logger.inject_lambda_context(log_event=True)
    def handler(event, context):
        logger.info("Hello")

    handler(lambda_event, lambda_context)

    # THEN logger should log event received from Lambda
    logged_event, _ = capture_multiple_logging_statements_output(stdout)
    assert logged_event["message"] == lambda_event


def test_inject_lambda_context_with_additional_args(lambda_context, stdout, service_name):
    # GIVEN Logger is initialized
    logger = Logger(service=service_name, stream=stdout)

    # AND a handler that use additional parameters
    @logger.inject_lambda_context
    def handler(event, context, planet, str_end="."):
        logger.info(f"Hello {planet}{str_end}")

    handler({}, lambda_context, "World", str_end="!")

    # THEN the decorator should included them
    log = capture_logging_output(stdout)

    assert log["message"] == "Hello World!"


def test_set_package_logger_handler_with_powertools_debug_env_var(stdout, monkeypatch: pytest.MonkeyPatch):
    # GIVEN POWERTOOLS_DEBUG is set
    monkeypatch.setenv(constants.POWERTOOLS_DEBUG_ENV, "1")
    logger = logging.getLogger("aws_lambda_powertools")

    # WHEN set_package_logger is used at initialization
    # and any Powertools for AWS Lambda (Python) operation is used (e.g., Tracer)
    set_package_logger_handler(stream=stdout)
    Tracer(disabled=True)

    # THEN Tracer debug log statement should be logged
    output = stdout.getvalue()
    assert "Tracing has been disabled" in output
    assert logger.level == logging.DEBUG


def test_powertools_debug_env_var_warning(monkeypatch: pytest.MonkeyPatch):
    # GIVEN POWERTOOLS_DEBUG is set
    monkeypatch.setenv(constants.POWERTOOLS_DEBUG_ENV, "1")
    warning_message = "POWERTOOLS_DEBUG environment variable is enabled. Setting logging level to DEBUG."

    # WHEN set_package_logger is used at initialization
    # THEN a warning should be emitted
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("default")
        set_package_logger_handler()
        assert len(w) == 1
        assert str(w[0].message) == warning_message


def test_logger_log_uncaught_exceptions(service_name, stdout):
    # GIVEN an initialized Logger is set with log_uncaught_exceptions
    logger = Logger(service=service_name, stream=stdout, log_uncaught_exceptions=True)

    # WHEN Python's exception hook is inspected
    exception_hook = sys.excepthook

    # THEN it should contain our custom exception hook with a copy of our logger
    assert isinstance(exception_hook, functools.partial)
    assert exception_hook.keywords.get("logger") == logger
