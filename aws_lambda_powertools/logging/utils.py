import logging
from typing import List, Optional, TypeVar

from .logger import Logger

PowertoolsLogger = TypeVar("PowertoolsLogger", bound=Logger)


def copy_config_to_registered_loggers(
    source_logger: PowertoolsLogger, exclude: Optional[List[str]] = None, include: Optional[List[str]] = None
) -> None:
    """Enable powertools logging for imported libraries.

    Attach source logger handlers to external loggers.
    Modify logger level based on source logger attribute.
    """
    registered_loggers = _find_registered_loggers(source_logger, exclude, include)
    for logger in registered_loggers:
        _configure_logger(source_logger, logger)


def _include_registered_loggers_filter(logger_list: List[str]):
    return [
        logging.getLogger(name) for name in logging.root.manager.loggerDict if "." not in name and name in logger_list
    ]


def _exclude_registered_loggers_filter(logger_list: List[str]) -> List[logging.Logger]:
    return [
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if "." not in name and name not in logger_list
    ]


def _find_registered_loggers(
    source_logger: PowertoolsLogger, exclude: Optional[List[str]] = None, include: Optional[List[str]] = None
) -> List[logging.Logger]:
    """Filter root loggers based on provided parameters.

    Ensure powertools logger itself is excluded from final list.
    """
    root_loggers = []
    if include and not exclude:
        root_loggers = _include_registered_loggers_filter(logger_list=include)
    elif include and exclude:
        exclude = [source_logger.name, *exclude]
        root_loggers = _include_registered_loggers_filter(logger_list=list(set(include) - set(exclude)))
    elif not include and exclude:
        exclude = [source_logger.name, *exclude]
        root_loggers = _exclude_registered_loggers_filter(logger_list=exclude)
    else:
        root_loggers = _exclude_registered_loggers_filter(logger_list=[source_logger.name])

    source_logger.debug(f"Filtered root loggers: {root_loggers}")
    return root_loggers


def _configure_logger(source_logger: PowertoolsLogger, logger: logging.Logger) -> None:
    logger.handlers = []
    logger.setLevel(source_logger.level)
    source_logger.debug(f"Logger {logger} reconfigured to use logging level {source_logger.level}")
    for source_handler in source_logger.handlers:
        logger.addHandler(source_handler)
        source_logger.debug(f"Logger {logger} reconfigured to use {source_handler}")
