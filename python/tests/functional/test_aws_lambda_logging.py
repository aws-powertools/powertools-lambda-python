"""aws_lambda_logging tests."""
import io
import json
import logging

from pytest import fixture, mark, yield_fixture

from aws_lambda_powertools.logging.aws_lambda_logging import setup


@fixture
def stdout():
    return io.StringIO()


@fixture
def handler(stdout):
    return logging.StreamHandler(stdout)


@fixture
def logger():
    return logging.getLogger(__name__)


@yield_fixture
def root_logger(handler):
    logging.root.addHandler(handler)
    yield logging.root
    logging.root.removeHandler(handler)


@mark.parametrize("level", ["DEBUG", "WARNING", "ERROR", "INFO", "CRITICAL"])
def test_setup_with_valid_log_levels(root_logger, logger, stdout, level):
    setup(level, request_id="request id!", another="value")

    logger.critical("This is a test")

    log_dict = json.loads(stdout.getvalue())

    check_log_dict(log_dict)

    assert "CRITICAL" == log_dict["level"]
    assert "This is a test" == log_dict["message"]
    assert "request id!" == log_dict["request_id"]
    assert "exception" not in log_dict


def test_logging_exception_traceback(root_logger, logger, stdout):
    setup("DEBUG", request_id="request id!", another="value")

    try:
        raise Exception("Boom")
    except Exception:
        logger.exception("This is a test")

    log_dict = json.loads(stdout.getvalue())

    check_log_dict(log_dict)
    assert "exception" in log_dict


def test_setup_with_invalid_log_level(root_logger, logger, stdout):
    setup("not a valid log level")  # writes a log event

    log_dict = json.loads(stdout.getvalue())

    check_log_dict(log_dict)


def check_log_dict(log_dict):
    assert "timestamp" in log_dict
    assert "level" in log_dict
    assert "location" in log_dict
    assert "message" in log_dict


def test_setup_with_bad_level_does_not_fail():
    setup("DBGG", request_id="request id!", another="value")


def test_with_dict_message(root_logger, logger, stdout):
    setup("DEBUG", another="value")

    msg = {"x": "isx"}
    logger.critical(msg)

    log_dict = json.loads(stdout.getvalue())

    assert msg == log_dict["message"]


def test_with_json_message(root_logger, logger, stdout):
    setup("DEBUG", another="value")

    msg = {"x": "isx"}
    logger.critical(json.dumps(msg))

    log_dict = json.loads(stdout.getvalue())

    assert msg == log_dict["message"]


def test_with_unserialisable_value_in_message(root_logger, logger, stdout):
    setup("DEBUG", another="value")

    class X:
        pass

    msg = {"x": X()}
    logger.critical(msg)

    log_dict = json.loads(stdout.getvalue())

    assert log_dict["message"]["x"].startswith("<")
