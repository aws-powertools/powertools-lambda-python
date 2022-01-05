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
        WARNING = 30
        CRITICAL = 50

    return LogLevel


@pytest.fixture
def logger(stdout, log_level):
    def _logger():
        logging.basicConfig(stream=stdout, level=log_level.NOTSET.value)
        logger = logging.getLogger(name=service_name())
        return logger

    return _logger


def capture_logging_output(stdout):
    return json.loads(stdout.getvalue().strip())


def capture_multiple_logging_statements_output(stdout):
    return [json.loads(line.strip()) for line in stdout.getvalue().split("\n") if line]


def service_name():
    chars = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(chars) for _ in range(15))


def test_copy_config_to_ext_loggers(stdout, logger, log_level):

    msg = "test message"

    # GIVEN a external logger and powertools logger initialized
    logger_1 = logger()
    logger_2 = logger()

    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to ALL external loggers AND our external logger used
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger)
    logger_1.info(msg)
    logger_2.info(msg)
    logs = capture_multiple_logging_statements_output(stdout)

    # THEN
    for index, logger in enumerate([logger_1, logger_2]):
        assert len(logger.handlers) == 1
        assert type(logger.handlers[0]) is logging.StreamHandler
        assert type(logger.handlers[0].formatter) is formatter.LambdaPowertoolsFormatter
        assert logger.level == log_level.INFO.value
        assert logs[index]["message"] == msg
        assert logs[index]["level"] == log_level.INFO.name


def test_copy_config_to_ext_loggers_include(stdout, logger, log_level):

    msg = "test message"

    # GIVEN a external logger and powertools logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to ALL external loggers AND our external logger used
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, include={logger.name})
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
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, include={"non-existing-logger"})

    # THEN
    assert not logger.handlers


def test_copy_config_to_ext_loggers_exclude(stdout, logger, log_level):

    # GIVEN a external logger and powertools logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to ALL external loggers AND our external logger used
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, exclude={logger.name})

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
        source_logger=powertools_logger, include={logger_1.name, logger_2.name}, exclude={logger_1.name}
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


def test_copy_config_to_ext_loggers_clean_old_handlers(stdout, logger, log_level):

    # GIVEN a external logger with handler and powertools logger initialized
    logger = logger()
    handler = logging.FileHandler("logfile")
    logger.addHandler(handler)
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to ALL external loggers AND our external logger used
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger)

    # THEN
    assert len(logger.handlers) == 1
    assert type(logger.handlers[0]) is logging.StreamHandler
    assert type(logger.handlers[0].formatter) is formatter.LambdaPowertoolsFormatter


def test_copy_config_to_ext_loggers_custom_log_level(stdout, logger, log_level):

    msg = "test message"

    # GIVEN a external logger and powertools logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.CRITICAL.value, stream=stdout)
    level = log_level.WARNING.name

    # WHEN configuration copied from powertools logger to ALL external loggers
    # AND our external logger used with custom log_level
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, include={logger.name}, log_level=level)
    logger.warning(msg)
    log = capture_logging_output(stdout)

    # THEN
    assert len(logger.handlers) == 1
    assert type(logger.handlers[0]) is logging.StreamHandler
    assert type(logger.handlers[0].formatter) is formatter.LambdaPowertoolsFormatter
    assert powertools_logger.level == log_level.CRITICAL.value
    assert logger.level == log_level.WARNING.value
    assert log["message"] == msg
    assert log["level"] == log_level.WARNING.name
