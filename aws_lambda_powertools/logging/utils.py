import logging
from typing import List, Optional, TypeVar

from .logger import Logger

PowertoolsLogger = TypeVar("PowertoolsLogger", bound=Logger)


def copy_config_to_registered_loggers(
    source_logger: PowertoolsLogger, exclude: Optional[List[str]] = None, include: Optional[List[str]] = None
):
    root_loggers = [
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if "." not in name and name != source_logger.name
    ]
    source_logger.debug(f"Found registered root loggers: {root_loggers}")
    if include and not exclude:
        root_loggers = [logger for logger in root_loggers if logger.name in include]
    elif not include and exclude:
        root_loggers = [logger for logger in root_loggers if logger.name not in exclude]
    elif include and exclude:
        root_loggers = [logger for logger in root_loggers if logger.name in include and logger.name not in exclude]

    source_logger.debug(f"Filtered root loggers: {root_loggers}")
    for logger in root_loggers:
        logger.handlers = []
        logger.setLevel(source_logger.level)
        for source_handler in source_logger.handlers:
            logger.addHandler(source_handler)
