import io
import json
import logging
import random
import string
from enum import Enum

import pytest

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import formatter, utils


@pytest.fixture
def stdout():
    return io.StringIO()


@pytest.fixture
def log_level():
    class LogLevel(Enum):
        NOTSET = 0
        INFO = 20

    return LogLevel


def capture_logging_output(stdout):
    return json.loads(stdout.getvalue().strip())


def service_name():
    chars = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(chars) for _ in range(15))


@pytest.fixture
def logger(stdout, log_level):
    def _logger():
        logging.basicConfig(stream=stdout, level=log_level.NOTSET.value)
        logger = logging.getLogger(name=service_name())
        return logger

    return _logger


def test_copy_config_to_ext_loggers(stdout, logger, log_level):

    msg = "test message"

    # GIVEN a external logger and powertools logger initialized
    logger = logger()
    logger_initial_handlers = logger.handlers.copy()
    logger_initial_level = logger.level
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to ALL external loggers AND our external logger used
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger)
    logger.info(msg)
    log = capture_logging_output(stdout)

    # THEN
    assert not logger_initial_handlers
    assert logger_initial_level == log_level.NOTSET.value
    assert len(logger.handlers) == 1
    assert type(logger.handlers[0]) is logging.StreamHandler
    assert type(logger.handlers[0].formatter) is formatter.LambdaPowertoolsFormatter
    assert logger.level == log_level.INFO.value
    assert log["message"] == msg
    assert log["level"] == log_level.INFO.name


def test_copy_config_to_ext_loggers_include(stdout, logger, log_level):

    msg = "test message"

    # GIVEN a external logger and powertools logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to ALL external loggers AND our external logger used
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, include=[logger.name])
    logger.info(msg)
    log = capture_logging_output(stdout)

    # THEN
    assert len(logger.handlers) == 1
    assert type(logger.handlers[0]) is logging.StreamHandler
    assert type(logger.handlers[0].formatter) is formatter.LambdaPowertoolsFormatter
    assert logger.level == log_level.INFO.value
    assert log["message"] == msg
    assert log["level"] == log_level.INFO.name


def test_copy_config_to_ext_loggers_wrong_include(stdout, logger, log_level):

    # GIVEN a external logger and powertools logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to ALL external loggers AND our external logger used
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, include=["non-existing-logger"])

    # THEN
    assert not logger.handlers


def test_copy_config_to_ext_loggers_exclude(stdout, logger, log_level):

    # GIVEN a external logger and powertools logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to ALL external loggers AND our external logger used
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, exclude=[logger.name])

    # THEN
    assert not logger.handlers


def test_copy_config_to_ext_loggers_include_exclude(stdout, logger, log_level):

    msg = "test message"

    # GIVEN a external logger and powertools logger initialized
    logger_1 = logger()
    logger_2 = logger()

    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to ALL external loggers AND our external logger used
    utils.copy_config_to_registered_loggers(
        source_logger=powertools_logger, include=[logger_1.name, logger_2.name], exclude=[logger_1.name]
    )
    logger_2.info(msg)
    log = capture_logging_output(stdout)
    # THEN
    assert not logger_1.handlers
    assert len(logger_2.handlers) == 1
    assert type(logger_2.handlers[0]) is logging.StreamHandler
    assert type(logger_2.handlers[0].formatter) is formatter.LambdaPowertoolsFormatter
    assert logger_2.level == log_level.INFO.value
    assert log["message"] == msg
    assert log["level"] == log_level.INFO.name
