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
        logging.basicConfig(stream=stdout, level=log_level.INFO.value)
        return logging.getLogger(name=service_name())

    return _logger


def capture_logging_output(stdout):
    return json.loads(stdout.getvalue().strip())


def capture_multiple_logging_statements_output(stdout):
    return [json.loads(line.strip()) for line in stdout.getvalue().split("\n") if line]


def service_name():
    chars = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(chars) for _ in range(15))


def test_copy_config_to_ext_loggers(stdout, logger, log_level):
    # GIVEN two external loggers and Powertools for AWS Lambda (Python) logger initialized
    logger_1 = logger()
    logger_2 = logger()

    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from Powertools for AWS Lambda (Python) logger to ALL external loggers
    # AND external loggers used
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger)
    msg = "test message1"
    logger_1.info(msg)
    logger_2.info(msg)
    logs = capture_multiple_logging_statements_output(stdout)

    # THEN all external loggers used Powertools for AWS Lambda (Python) handler, formatter and log level
    for index, logger in enumerate([logger_1, logger_2]):
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert isinstance(logger.handlers[0].formatter, formatter.LambdaPowertoolsFormatter)
        assert logger.level == log_level.INFO.value
        assert logs[index]["message"] == msg
        assert logs[index]["level"] == log_level.INFO.name


def test_copy_config_to_ext_loggers_include(stdout, logger, log_level):
    # GIVEN an external logger and Powertools for AWS Lambda (Python) logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from Powertools for AWS Lambda (Python) logger to INCLUDED external loggers
    # AND our external logger used
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, include={logger.name})
    msg = "test message2"
    logger.info(msg)
    log = capture_logging_output(stdout)

    # THEN included external loggers used Powertools for AWS Lambda (Python) handler, formatter and log level.
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert isinstance(logger.handlers[0].formatter, formatter.LambdaPowertoolsFormatter)
    assert logger.level == log_level.INFO.value
    assert log["message"] == msg
    assert log["level"] == log_level.INFO.name


def test_copy_config_to_ext_loggers_wrong_include(stdout, logger, log_level):
    # GIVEN an external logger and Powertools for AWS Lambda (Python) for AWS Lambda (Python) logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from Powertools for AWS Lambda (Python) for AWS Lambda (Python) logger
    # to INCLUDED NON EXISTING external loggers
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, include={"non-existing-logger"})

    # THEN existing external logger is not modified
    assert not logger.handlers


def test_copy_config_to_ext_loggers_exclude(stdout, logger, log_level):
    # GIVEN an external logger and Powertools for AWS Lambda (Python) logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from Powertools for AWS Lambda (Python) logger to ALL BUT external logger
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, exclude={logger.name})

    # THEN external logger is not modified
    assert not logger.handlers


def test_copy_config_to_ext_loggers_include_exclude(stdout, logger, log_level):
    # GIVEN two external loggers and Powertools for AWS Lambda (Python) logger initialized
    logger_1 = logger()
    logger_2 = logger()

    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from Powertools for AWS Lambda (Python) logger to INCLUDED external loggers
    # AND external logger_1 is also in EXCLUDE list
    utils.copy_config_to_registered_loggers(
        source_logger=powertools_logger,
        include={logger_1.name, logger_2.name},
        exclude={logger_1.name},
    )
    msg = "test message3"
    logger_2.info(msg)
    log = capture_logging_output(stdout)

    # THEN logger_1 is not modified and Logger_2 used Powertools for AWS Lambda (Python) handler, formatter and log
    # level
    assert not logger_1.handlers
    assert len(logger_2.handlers) == 1
    assert isinstance(logger_2.handlers[0], logging.StreamHandler)
    assert isinstance(logger_2.handlers[0].formatter, formatter.LambdaPowertoolsFormatter)
    assert logger_2.level == log_level.INFO.value
    assert log["message"] == msg
    assert log["level"] == log_level.INFO.name


def test_copy_config_to_ext_loggers_clean_old_handlers(stdout, logger, log_level):
    # GIVEN an external logger with handler and Powertools for AWS Lambda (Python) logger initialized
    logger = logger()
    handler = logging.NullHandler()
    logger.addHandler(handler)
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from Powertools for AWS Lambda (Python) logger to ALL external loggers
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger)

    # THEN old logger's handler removed and Powertools for AWS Lambda (Python) configuration used instead
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert isinstance(logger.handlers[0].formatter, formatter.LambdaPowertoolsFormatter)


@pytest.mark.parametrize("level_to_set", ["WARNING", 30])
def test_copy_config_to_ext_loggers_custom_log_level(stdout, logger, log_level, level_to_set):
    # GIVEN an external logger and Powertools for AWS Lambda (Python) logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.CRITICAL.value, stream=stdout)

    # WHEN configuration copied from Powertools for AWS Lambda (Python) logger to INCLUDED external logger
    # AND external logger used with custom log_level
    utils.copy_config_to_registered_loggers(
        source_logger=powertools_logger,
        include={logger.name},
        log_level=level_to_set,
    )
    msg = "test message4"
    logger.warning(msg)
    log = capture_logging_output(stdout)

    # THEN external logger used Powertools for AWS Lambda (Python) handler, formatter and CUSTOM log level.
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert isinstance(logger.handlers[0].formatter, formatter.LambdaPowertoolsFormatter)
    assert powertools_logger.level == log_level.CRITICAL.value
    assert logger.level == log_level.WARNING.value
    assert log["message"] == msg
    assert log["level"] == log_level.WARNING.name


def test_copy_config_to_ext_loggers_should_not_break_append_keys(stdout, log_level):
    # GIVEN Powertools for AWS Lambda (Python) logger initialized
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from Powertools for AWS Lambda (Python) logger to ALL external loggers
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger)

    # THEN append_keys should not raise an exception
    powertools_logger.append_keys(key="value")


def test_copy_config_to_parent_loggers_only(stdout):
    # GIVEN Powertools for AWS Lambda (Python) Logger and Child Logger are initialized
    # and Powertools for AWS Lambda (Python) Logger config is copied over
    service = service_name()
    child = Logger(stream=stdout, service=service, child=True)
    parent = Logger(stream=stdout, service=service)
    utils.copy_config_to_registered_loggers(source_logger=parent)

    # WHEN either parent or child logger append keys
    child.append_keys(customer_id="value")
    parent.append_keys(user_id="value")
    parent.info("Logger message")
    child.info("Child logger message")

    # THEN both custom keys should be propagated bi-directionally in parent and child loggers
    # as child logger won't be touched when config is being copied
    parent_log, child_log = capture_multiple_logging_statements_output(stdout)
    assert "customer_id" in parent_log, child_log
    assert "user_id" in parent_log, child_log
    assert child.parent.name == service


def test_copy_config_to_parent_loggers_only_with_exclude(stdout):
    # GIVEN Powertools for AWS Lambda (Python) Logger and Child Logger are initialized
    # and Powertools for AWS Lambda (Python) Logger config is copied over with exclude set
    service = service_name()
    child = Logger(stream=stdout, service=service, child=True)
    parent = Logger(stream=stdout, service=service)
    utils.copy_config_to_registered_loggers(source_logger=parent, exclude={"test"})

    # WHEN either parent or child logger append keys
    child.append_keys(customer_id="value")
    parent.append_keys(user_id="value")
    parent.info("Logger message")
    child.info("Child logger message")

    # THEN both custom keys should be propagated bi-directionally in parent and child loggers
    # as child logger won't be touched when config is being copied
    parent_log, child_log = capture_multiple_logging_statements_output(stdout)
    assert "customer_id" in parent_log, child_log
    assert "user_id" in parent_log, child_log
    assert child.parent.name == service


def test_copy_config_to_ext_loggers_no_duplicate_logs(stdout, logger, log_level):
    # GIVEN an root logger, external logger and Powertools for AWS Lambda (Python) logger initialized

    root_logger = logging.getLogger()
    handler = logging.StreamHandler(stdout)
    formatter = logging.Formatter('{"message": "%(message)s"}')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    logger = logger()

    powertools_logger = Logger(service=service_name(), level=log_level.CRITICAL.value, stream=stdout)
    level = log_level.WARNING.name

    # WHEN configuration copied from Powertools for AWS Lambda (Python) logger
    # AND external logger used with custom log_level
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, include={logger.name}, log_level=level)
    msg = "test message4"
    logger.warning(msg)

    # THEN no root logger logs AND log is not duplicated
    logs = capture_multiple_logging_statements_output(stdout)
    assert {"message": msg} not in logs
    assert sum(msg in log.values() for log in logs) == 1


def test_logger_name_is_included_during_copy(stdout, logger, log_level):
    # GIVEN two external loggers and Powertools for AWS Lambda (Python) logger initialized
    logger_1: logging.Logger = logger()
    logger_2: logging.Logger = logger()
    msg = "test message1"

    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from Powertools for AWS Lambda (Python) logger to ALL external loggers
    # AND external loggers used
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, include={logger_1.name, logger_2.name})
    logger_1.info(msg)
    logger_2.info(msg)
    powertools_logger.info(msg)

    logger1_log, logger2_log, pt_log = capture_multiple_logging_statements_output(stdout)

    # THEN name attribute should be present in all loggers
    assert logger1_log["name"] == logger_1.name
    assert logger2_log["name"] == logger_2.name
    assert pt_log["name"] == powertools_logger.name
