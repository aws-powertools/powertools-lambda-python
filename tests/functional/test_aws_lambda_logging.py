"""aws_lambda_logging tests."""
import io
import json

import pytest

from aws_lambda_powertools import Logger


@pytest.fixture
def stdout():
    return io.StringIO()


@pytest.mark.parametrize("level", ["DEBUG", "WARNING", "ERROR", "INFO", "CRITICAL"])
def test_setup_with_valid_log_levels(stdout, level):
    logger = Logger(level=level, stream=stdout, request_id="request id!", another="value")
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


def test_logging_exception_traceback(stdout):
    logger = Logger(level="DEBUG", stream=stdout)

    try:
        raise ValueError("Boom")
    except ValueError:
        logger.exception("A value error occurred")

    log_dict = json.loads(stdout.getvalue())

    check_log_dict(log_dict)
    assert "ERROR" == log_dict["level"]
    assert "exception" in log_dict


def test_setup_with_invalid_log_level(stdout):
    with pytest.raises(ValueError) as e:
        Logger(level="not a valid log level")
        assert "Unknown level" in e.value.args[0]


def check_log_dict(log_dict):
    assert "timestamp" in log_dict
    assert "level" in log_dict
    assert "location" in log_dict
    assert "message" in log_dict


def test_with_dict_message(stdout):
    logger = Logger(level="DEBUG", stream=stdout)

    msg = {"x": "isx"}
    logger.critical(msg)

    log_dict = json.loads(stdout.getvalue())

    assert msg == log_dict["message"]


def test_with_json_message(stdout):
    logger = Logger(stream=stdout)

    msg = {"x": "isx"}
    logger.info(json.dumps(msg))

    log_dict = json.loads(stdout.getvalue())

    assert msg == log_dict["message"]


def test_with_unserializable_value_in_message(stdout):
    logger = Logger(level="DEBUG", stream=stdout)

    class Unserializable:
        pass

    msg = {"x": Unserializable()}
    logger.debug(msg)

    log_dict = json.loads(stdout.getvalue())

    assert log_dict["message"]["x"].startswith("<")


def test_with_unserializable_value_in_message_custom(stdout):
    class Unserializable:
        pass

    # GIVEN a custom json_default
    logger = Logger(level="DEBUG", stream=stdout, json_default=lambda o: f"<non-serializable: {type(o).__name__}>")

    # WHEN we log a message
    logger.debug({"x": Unserializable()})

    log_dict = json.loads(stdout.getvalue())

    # THEN json_default should not be in the log message and the custom unserializable handler should be used
    assert log_dict["message"]["x"] == "<non-serializable: Unserializable>"
    assert "json_default" not in log_dict


def test_log_dict_key_seq(stdout):
    # GIVEN any logger configuration
    logger = Logger(level="INFO", stream=stdout, another="xxx")

    # WHEN logging a message
    logger.info("Message")

    log_dict: dict = json.loads(stdout.getvalue())

    # THEN the key sequence should be `timestamp,level,location,message`
    assert ",".join(list(log_dict.keys())[:4]) == "timestamp,level,location,message"
