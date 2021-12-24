import logging
from typing import Callable, List, Optional, TypeVar

from .logger import Logger

PowertoolsLogger = TypeVar("PowertoolsLogger", bound=Logger)


def copy_config_to_registered_loggers(
    source_logger: PowertoolsLogger,
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
) -> None:
    """Enable powertools logging for imported libraries.

    Attach source logger handlers to external loggers.
    Modify logger level based on source logger attribute.
    Ensure powertools logger itself is excluded from registered list.
    """

    if include and not exclude:
        loggers = include
        filter_func = _include_registered_loggers_filter
    elif include and exclude:
        exclude = [source_logger.name, *exclude]
        loggers = list(set(include) - set(exclude))
        filter_func = _include_registered_loggers_filter
    elif not include and exclude:
        loggers = [source_logger.name, *exclude]
        filter_func = _exclude_registered_loggers_filter
    else:
        loggers = [source_logger.name]
        filter_func = _exclude_registered_loggers_filter

    registered_loggers = _find_registered_loggers(source_logger, loggers, filter_func)
    for logger in registered_loggers:
        _configure_logger(source_logger, logger)


def _include_registered_loggers_filter(loggers: List[str]):
    return [logging.getLogger(name) for name in logging.root.manager.loggerDict if "." not in name and name in loggers]


def _exclude_registered_loggers_filter(loggers: List[str]) -> List[logging.Logger]:
    return [
        logging.getLogger(name) for name in logging.root.manager.loggerDict if "." not in name and name not in loggers
    ]


def _find_registered_loggers(
    source_logger: PowertoolsLogger, loggers: List[str], filter_func: Callable
) -> List[logging.Logger]:
    """Filter root loggers based on provided parameters."""
    root_loggers = filter_func(loggers)
    source_logger.debug(f"Filtered root loggers: {root_loggers}")
    return root_loggers


def _configure_logger(source_logger: PowertoolsLogger, logger: logging.Logger) -> None:
    logger.handlers = []
    logger.setLevel(source_logger.level)
    source_logger.debug(f"Logger {logger} reconfigured to use logging level {source_logger.level}")
    for source_handler in source_logger.handlers:
        logger.addHandler(source_handler)
        source_logger.debug(f"Logger {logger} reconfigured to use {source_handler}")
