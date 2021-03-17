"""aws_lambda_logging tests."""
import io
import json
import random
import string

import pytest

from aws_lambda_powertools import Logger


@pytest.fixture
def stdout():
    return io.StringIO()


@pytest.fixture
def service_name():
    chars = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(chars) for _ in range(15))


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
    assert log_dict["location"] == "[test_log_custom_formatting] test_aws_lambda_logging"
    assert log_dict["timestamp"] == "fake-datefmt"


def test_log_dict_key_strip_nones(stdout, service_name):
    # GIVEN a logger confirmation where we set `location` and `timestamp` to None
    # Note: level, sampling_rate and service can not be suppressed
    logger = Logger(stream=stdout, level=None, location=None, timestamp=None, sampling_rate=None, service=None)

    # WHEN logging a message
    logger.info("foo")

    log_dict: dict = json.loads(stdout.getvalue())

    # THEN the keys should only include `level`, `message`, `service`, `sampling_rate`
    assert sorted(log_dict.keys()) == ["level", "message", "sampling_rate", "service"]
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
