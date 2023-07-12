"""aws_lambda_logging tests."""
import io
import json
import os
import random
import re
import string
import time

import pytest

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.formatters.datadog import DatadogLogFormatter


@pytest.fixture
def stdout():
    return io.StringIO()


@pytest.fixture
def service_name():
    chars = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(chars) for _ in range(15))


def capture_logging_output(stdout):
    return json.loads(stdout.getvalue().strip())


@pytest.mark.parametrize("level", ["DEBUG", "WARNING", "ERROR", "INFO", "CRITICAL"])
def test_setup_with_valid_log_levels(stdout, level, service_name):
    logger = Logger(service=service_name, level=level, stream=stdout, request_id="request id!", another="value")
    msg = "This is a test"
    log_command = {
        "INFO": logger.info,
        "ERROR": logger.error,
        "WARNING": logger.warning,
        "DEBUG": logger.debug,
        "CRITICAL": logger.critical,
    }

    log_message = log_command[level]
    log_message(msg)

    log_dict = json.loads(stdout.getvalue().strip())

    check_log_dict(log_dict)

    assert level == log_dict["level"]
    assert "This is a test" == log_dict["message"]
    assert "request id!" == log_dict["request_id"]
    assert "exception" not in log_dict


def test_logging_exception_traceback(stdout, service_name):
    logger = Logger(service=service_name, level="DEBUG", stream=stdout)

    try:
        raise ValueError("Boom")
    except ValueError:
        logger.exception("A value error occurred")

    log_dict = json.loads(stdout.getvalue())

    check_log_dict(log_dict)
    assert "ERROR" == log_dict["level"]
    assert "exception" in log_dict


def test_setup_with_invalid_log_level(stdout, service_name):
    with pytest.raises(ValueError) as e:
        Logger(service=service_name, level="not a valid log level")
        assert "Unknown level" in e.value.args[0]


def check_log_dict(log_dict):
    assert "timestamp" in log_dict
    assert "level" in log_dict
    assert "location" in log_dict
    assert "message" in log_dict


def test_with_dict_message(stdout, service_name):
    logger = Logger(service=service_name, level="DEBUG", stream=stdout)

    msg = {"x": "isx"}
    logger.critical(msg)

    log_dict = json.loads(stdout.getvalue())

    assert msg == log_dict["message"]


def test_with_json_message(stdout, service_name):
    logger = Logger(service=service_name, stream=stdout)

    msg = {"x": "isx"}
    logger.info(json.dumps(msg))

    log_dict = json.loads(stdout.getvalue())

    assert msg == log_dict["message"]


def test_with_unserializable_value_in_message(stdout, service_name):
    logger = Logger(service=service_name, level="DEBUG", stream=stdout)

    class Unserializable:
        pass

    msg = {"x": Unserializable()}
    logger.debug(msg)

    log_dict = json.loads(stdout.getvalue())

    assert log_dict["message"]["x"].startswith("<")


def test_with_unserializable_value_in_message_custom(stdout, service_name):
    class Unserializable:
        pass

    # GIVEN a custom json_default
    logger = Logger(
        service=service_name,
        level="DEBUG",
        stream=stdout,
        json_default=lambda o: f"<non-serializable: {type(o).__name__}>",
    )

    # WHEN we log a message
    logger.debug({"x": Unserializable()})

    log_dict = json.loads(stdout.getvalue())

    # THEN json_default should not be in the log message and the custom unserializable handler should be used
    assert log_dict["message"]["x"] == "<non-serializable: Unserializable>"
    assert "json_default" not in log_dict


def test_log_dict_key_seq(stdout, service_name):
    # GIVEN the default logger configuration
    logger = Logger(service=service_name, stream=stdout)

    # WHEN logging a message
    logger.info("Message")

    log_dict: dict = json.loads(stdout.getvalue())

    # THEN the beginning key sequence must be `level,location,message,timestamp`
    assert ",".join(list(log_dict.keys())[:4]) == "level,location,message,timestamp"


def test_log_dict_key_custom_seq(stdout, service_name):
    # GIVEN a logger configuration with log_record_order set to ["message"]
    logger = Logger(service=service_name, stream=stdout, log_record_order=["message"])

    # WHEN logging a message
    logger.info("Message")

    log_dict: dict = json.loads(stdout.getvalue())

    # THEN the first key should be "message"
    assert list(log_dict.keys())[0] == "message"


def test_log_custom_formatting(stdout, service_name):
    # GIVEN a logger where we have a custom `location`, 'datefmt' format
    logger = Logger(service=service_name, stream=stdout, location="[%(funcName)s] %(module)s", datefmt="fake-datefmt")

    # WHEN logging a message
    logger.info("foo")

    log_dict: dict = json.loads(stdout.getvalue())

    # THEN the `location` and "timestamp" should match the formatting
    assert log_dict["location"] == "[test_log_custom_formatting] test_logger_powertools_formatter"
    assert log_dict["timestamp"] == "fake-datefmt"


def test_log_dict_key_strip_nones(stdout, service_name):
    # GIVEN a logger confirmation where we set `location` and `timestamp` to None
    # Note: level and service cannot be suppressed
    logger = Logger(stream=stdout, level=None, location=None, timestamp=None, sampling_rate=None, service=None)

    # WHEN logging a message
    logger.info("foo")

    log_dict: dict = json.loads(stdout.getvalue())

    # THEN the keys should only include `level`, `message`, `service`
    assert sorted(log_dict.keys()) == ["level", "message", "service"]
    assert log_dict["service"] == "service_undefined"


def test_log_dict_xray_is_present_when_tracing_is_enabled(stdout, monkeypatch, service_name):
    # GIVEN a logger is initialized within a Lambda function with X-Ray enabled
    trace_id = "1-5759e988-bd862e3fe1be46a994272793"
    trace_header = f"Root={trace_id};Parent=53995c3f42cd8ad8;Sampled=1"
    monkeypatch.setenv(name="_X_AMZN_TRACE_ID", value=trace_header)
    logger = Logger(service=service_name, stream=stdout)

    # WHEN logging a message
    logger.info("foo")

    log_dict: dict = json.loads(stdout.getvalue())

    # THEN `xray_trace_id`` key should be present
    assert log_dict["xray_trace_id"] == trace_id

    monkeypatch.delenv(name="_X_AMZN_TRACE_ID")


def test_log_dict_xray_is_not_present_when_tracing_is_disabled(stdout, monkeypatch, service_name):
    # GIVEN a logger is initialized within a Lambda function with X-Ray disabled (default)
    logger = Logger(service=service_name, stream=stdout)

    # WHEN logging a message
    logger.info("foo")

    log_dict: dict = json.loads(stdout.getvalue())

    # THEN `xray_trace_id`` key should not be present
    assert "xray_trace_id" not in log_dict


def test_log_dict_xray_is_updated_when_tracing_id_changes(stdout, monkeypatch, service_name):
    # GIVEN a logger is initialized within a Lambda function with X-Ray enabled
    trace_id = "1-5759e988-bd862e3fe1be46a994272793"
    trace_header = f"Root={trace_id};Parent=53995c3f42cd8ad8;Sampled=1"
    monkeypatch.setenv(name="_X_AMZN_TRACE_ID", value=trace_header)
    logger = Logger(service=service_name, stream=stdout)

    # WHEN logging a message
    logger.info("foo")

    # and Trace ID changes to mimick a new invocation
    trace_id_2 = "1-5759e988-bd862e3fe1be46a949393982437"
    trace_header_2 = f"Root={trace_id_2};Parent=53995c3f42cd8ad8;Sampled=1"
    monkeypatch.setenv(name="_X_AMZN_TRACE_ID", value=trace_header_2)

    logger.info("foo bar")

    log_dict, log_dict_2 = [json.loads(line.strip()) for line in stdout.getvalue().split("\n") if line]

    # THEN `xray_trace_id`` key should be different in both invocations
    assert log_dict["xray_trace_id"] == trace_id
    assert log_dict_2["xray_trace_id"] == trace_id_2

    monkeypatch.delenv(name="_X_AMZN_TRACE_ID")


def test_log_custom_std_log_attribute(stdout, service_name):
    # GIVEN a logger where we have a standard log attr process
    # https://docs.python.org/3/library/logging.html#logrecord-attributes
    logger = Logger(service=service_name, stream=stdout, process="%(process)d")

    # WHEN logging a message
    logger.info("foo")

    log_dict: dict = json.loads(stdout.getvalue())

    # THEN process key should be evaluated
    assert "%" not in log_dict["process"]


def test_log_in_utc(service_name):
    # GIVEN a logger where UTC TZ has been set
    logger = Logger(service=service_name, utc=True)

    # THEN logging formatter time converter should use gmtime fn
    assert logger._logger.handlers[0].formatter.converter == time.gmtime


@pytest.mark.parametrize("message", ["hello", 1.10, {}, [], True, object()])
def test_logging_various_primitives(stdout, service_name, message):
    # GIVEN a logger with default settings
    logger = Logger(service=service_name, stream=stdout)

    # WHEN logging a message of multiple common types
    # THEN it should raise no serialization/deserialization error
    logger.info(message)
    json.loads(stdout.getvalue())


def test_log_formatting(stdout, service_name):
    # GIVEN a logger with default settings
    logger = Logger(service=service_name, stream=stdout)

    # WHEN logging a message with formatting
    logger.info('["foo %s %d %s", null]', "bar", 123, [1, None])

    log_dict: dict = json.loads(stdout.getvalue())

    # THEN the formatting should be applied (NB. this is valid json, but hasn't be parsed)
    assert log_dict["message"] == '["foo bar 123 [1, None]", null]'


def test_log_json_indent_compact_indent(stdout, service_name, monkeypatch):
    # GIVEN a logger with default settings and WHEN POWERTOOLS_DEV is not set
    monkeypatch.delenv(name="POWERTOOLS_DEV", raising=False)
    logger = Logger(service=service_name, stream=stdout)
    logger.info("Test message")
    # THEN the json should not have multiple lines
    new_lines = stdout.getvalue().count(os.linesep)
    assert new_lines == 1


def test_log_json_pretty_indent(stdout, service_name, monkeypatch):
    # GIVEN a logger with default settings and WHEN POWERTOOLS_DEV=="true"
    monkeypatch.setenv(name="POWERTOOLS_DEV", value="true")
    logger = Logger(service=service_name, stream=stdout)
    logger.info("Test message")
    # THEN the json should contain more than line
    new_lines = stdout.getvalue().count(os.linesep)
    assert new_lines > 1


def test_datadog_formatter_use_rfc3339_date(stdout, service_name):
    # GIVEN Datadog Log Formatter is used
    logger = Logger(service=service_name, stream=stdout, logger_formatter=DatadogLogFormatter())
    RFC3339_REGEX = r"^((?:(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2}(?:\.\d+)?))(Z|[\+-]\d{2}:\d{2})?)$"

    # WHEN a log statement happens
    logger.info({})

    # THEN the timestamp uses RFC3339 by default
    log = capture_logging_output(stdout)

    assert re.fullmatch(RFC3339_REGEX, log["timestamp"])  # "2022-10-27T17:42:26.841+0200"
