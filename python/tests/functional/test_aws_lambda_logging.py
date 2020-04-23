"""aws_lambda_logging tests."""
import functools
import io
import json
import logging

import pytest

from aws_lambda_powertools.logging.logger import Logger


@pytest.fixture
def stdout():
    return io.StringIO()


@pytest.fixture
def handler(stdout):
    return logging.StreamHandler(stdout)


@pytest.fixture
def logger():
    return logging.getLogger(__name__)


@pytest.fixture
def root_logger(handler):
    logging.root.addHandler(handler)
    yield logging.root
    logging.root.removeHandler(handler)


@pytest.mark.parametrize("level", ["DEBUG", "WARNING", "ERROR", "INFO", "CRITICAL"])
def test_setup_with_valid_log_levels(root_logger, stdout, level):
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


def test_logging_exception_traceback(root_logger, stdout):
    logger = Logger(level="DEBUG", stream=stdout, request_id="request id!", another="value")

    try:
        raise Exception("Boom")
    except Exception:
        logger.exception("This is a test")

    log_dict = json.loads(stdout.getvalue())

    check_log_dict(log_dict)
    assert "exception" in log_dict


def test_setup_with_invalid_log_level(root_logger, logger, stdout):
    with pytest.raises(ValueError) as e:
        Logger(level="not a valid log level")
        assert "Unknown level" in e.value.args[0]


def check_log_dict(log_dict):
    assert "timestamp" in log_dict
    assert "level" in log_dict
    assert "location" in log_dict
    assert "message" in log_dict


def test_setup_with_bad_level_does_not_fail():
    Logger("DBGG", request_id="request id!", another="value")


def test_with_dict_message(root_logger, stdout):
    logger = Logger(level="DEBUG", stream=stdout)

    msg = {"x": "isx"}
    logger.critical(msg)

    log_dict = json.loads(stdout.getvalue())

    assert msg == log_dict["message"]


def test_with_json_message(root_logger, stdout):
    logger = Logger(stream=stdout)

    msg = {"x": "isx"}
    logger.info(json.dumps(msg))

    log_dict = json.loads(stdout.getvalue())

    assert msg == log_dict["message"]


def test_with_unserialisable_value_in_message(root_logger, stdout):
    logger = Logger(level="DEBUG", stream=stdout)

    class X:
        pass

    msg = {"x": X()}
    logger.debug(msg)

    log_dict = json.loads(stdout.getvalue())

    assert log_dict["message"]["x"].startswith("<")
