import io
import json
import logging
import random
import string
import warnings
from collections import namedtuple

import pytest

from aws_lambda_powertools import Metrics, set_package_logger_handler
from aws_lambda_powertools.logging.logger import set_package_logger
from aws_lambda_powertools.shared import constants


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


def test_package_logger_stream(stdout):
    # GIVEN package logger "aws_lambda_powertools" is explicitly set with no params
    set_package_logger(stream=stdout)

    # WHEN we add a dimension in Metrics feature
    my_metrics = Metrics(namespace="powertools")
    my_metrics.add_dimension(name="dimension", value="test")

    # THEN Metrics debug log statement should be logged
    output = stdout.getvalue()
    logger = logging.getLogger("aws_lambda_powertools")
    assert "Adding dimension:" in output
    assert logger.level == logging.DEBUG


def test_package_logger_format(capsys):
    # GIVEN package logger "aws_lambda_powertools" is explicitly
    # with a custom formatter
    formatter = logging.Formatter("message=%(message)s")
    set_package_logger(formatter=formatter)

    # WHEN we add a dimension in Metrics feature
    my_metrics = Metrics(namespace="powertools")
    my_metrics.add_dimension(name="dimension", value="test")

    # THEN Metrics debug log statement should be logged using `message=` format
    output = capsys.readouterr().out
    logger = logging.getLogger("aws_lambda_powertools")
    assert "message=" in output
    assert logger.level == logging.DEBUG


def test_set_package_logger_handler_with_powertools_debug_env_var(stdout, monkeypatch: pytest.MonkeyPatch):
    # GIVEN POWERTOOLS_DEBUG is set
    monkeypatch.setenv(constants.POWERTOOLS_DEBUG_ENV, "1")
    logger = logging.getLogger("aws_lambda_powertools")

    # WHEN set_package_logger is used at initialization
    # and any Powertools for AWS Lambda (Python) operation is used (e.g., Metrics add_dimension)
    set_package_logger_handler(stream=stdout)

    my_metrics = Metrics(namespace="powertools")
    my_metrics.add_dimension(name="dimension", value="test")

    # THEN Metrics debug log statement should be logged
    output = stdout.getvalue()
    assert "Adding dimension:" in output
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
