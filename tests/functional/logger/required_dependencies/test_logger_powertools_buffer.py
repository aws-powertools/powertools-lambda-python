"""aws_lambda_logging tests."""

import io
import json
import random
import string
from collections import namedtuple

import pytest

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.buffer import LoggerBufferConfig


@pytest.fixture
def lambda_context():
    lambda_context = {
        "function_name": "test",
        "memory_limit_in_mb": 128,
        "invoked_function_arn": "arn:aws:lambda:eu-west-1:809313241:function:test",
        "aws_request_id": "52fdfc07-2182-154f-163f-5f0f9a621d72",
    }

    return namedtuple("LambdaContext", lambda_context.keys())(*lambda_context.values())


def check_log_dict(log_dict):
    assert "timestamp" in log_dict
    assert "level" in log_dict
    assert "location" in log_dict
    assert "message" in log_dict


@pytest.fixture
def stdout():
    return io.StringIO()


@pytest.fixture
def service_name():
    chars = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(chars) for _ in range(15))


def capture_logging_output(stdout):
    return [json.loads(d.strip()) for d in stdout.getvalue().strip().split("\n")]


def test_logger_buffer_is_enabled():

    buffer_config = LoggerBufferConfig(max_size=10240)
    logger = Logger(level="INFO", buffer_config=buffer_config)

    leo = logger.info("A")

    assert leo is True


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
