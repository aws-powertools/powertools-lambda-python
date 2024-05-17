import logging
from typing import Callable, List, Optional, Set, Union

from .logger import Logger

PACKAGE_LOGGER = "aws_lambda_powertools"


def copy_config_to_registered_loggers(
    source_logger: Logger,
    log_level: Optional[Union[int, str]] = None,
    ignore_log_level=False,
    exclude: Optional[Set[str]] = None,
    include: Optional[Set[str]] = None,
) -> None:
    """Copies source Logger level and handler to all registered loggers for consistent formatting.

    Parameters
    ----------
    ignore_log_level
    source_logger : Logger
        Powertools for AWS Lambda (Python) Logger to copy configuration from
    log_level : Union[int, str], optional
        Logging level to set to registered loggers, by default uses source_logger logging level
    ignore_log_level: bool
        Whether to not touch log levels for discovered loggers. log_level param is disregarded when this is set.
    include : Optional[Set[str]], optional
        List of logger names to include, by default all registered loggers are included
    exclude : Optional[Set[str]], optional
        List of logger names to exclude, by default None
    """
    level = log_level or source_logger.log_level

    # Assumptions: Only take parent loggers not children (dot notation rule)
    # Steps:
    # 1. Default operation: Include all registered loggers
    # 2. Only include set? Only add Loggers in the list and ignore all else
    # 3. Include and exclude set? Add Logger if it’s in include and not in exclude
    # 4. Only exclude set? Ignore Logger in the excluding list

    # Exclude source and Powertools for AWS Lambda (Python) package logger by default
    # If source logger is a child ensure we exclude parent logger to not break child logger
    # from receiving/pushing updates to keys being added/removed
    source_logger_name = source_logger.name.split(".")[0]

    if exclude:
        exclude.update([source_logger_name, PACKAGE_LOGGER])
    else:
        exclude = {source_logger_name, PACKAGE_LOGGER}

    # Prepare loggers set
    if include:
        loggers = include.difference(exclude)
        filter_func = _include_registered_loggers_filter
    else:
        loggers = exclude
        filter_func = _exclude_registered_loggers_filter

    registered_loggers = _find_registered_loggers(source_logger, loggers, filter_func)
    for logger in registered_loggers:
        _configure_logger(source_logger=source_logger, logger=logger, level=level, ignore_log_level=ignore_log_level)


def _include_registered_loggers_filter(loggers: Set[str]):
    return [logging.getLogger(name) for name in logging.root.manager.loggerDict if "." not in name and name in loggers]


def _exclude_registered_loggers_filter(loggers: Set[str]) -> List[logging.Logger]:
    return [
        logging.getLogger(name) for name in logging.root.manager.loggerDict if "." not in name and name not in loggers
    ]


def _find_registered_loggers(
    source_logger: Logger,
    loggers: Set[str],
    filter_func: Callable[[Set[str]], List[logging.Logger]],
) -> List[logging.Logger]:
    """Filter root loggers based on provided parameters."""
    root_loggers = filter_func(loggers)
    source_logger.debug(f"Filtered root loggers: {root_loggers}")
    return root_loggers


def _configure_logger(
    source_logger: Logger,
    logger: logging.Logger,
    level: Union[int, str],
    ignore_log_level: bool = False,
) -> None:
    # customers may not want to copy the same log level from Logger to discovered loggers
    if not ignore_log_level:
        logger.setLevel(level)
        source_logger.debug(f"Logger {logger} reconfigured to use logging level {level}")

    logger.handlers = []
    logger.propagate = False  # ensure we don't propagate logs to existing loggers, #1073
    source_logger.append_keys(name="%(name)s")  # include logger name, see #1267

    for source_handler in source_logger.handlers:
        logger.addHandler(source_handler)
        source_logger.debug(f"Logger {logger} reconfigured to use {source_handler}")
