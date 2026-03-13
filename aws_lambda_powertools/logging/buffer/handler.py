from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aws_lambda_powertools.logging.buffer.functions import _check_minimum_buffer_log_level

if TYPE_CHECKING:
    from aws_lambda_powertools.logging.buffer.cache import LoggerBufferCache
    from aws_lambda_powertools.logging.buffer.config import LoggerBufferConfig
    from aws_lambda_powertools.logging.logger import Logger


class BufferingHandler(logging.Handler):
    """
    Handler that buffers logs from external libraries using the source logger's buffer.

    The handler intercepts log records from external libraries and
    stores them in the source logger's buffer using the same tracer_id mechanism.
    Logs above the buffer verbosity threshold are emitted directly through the source logger.
    Logs at or below the threshold are buffered and flushed together with application logs.
    """

    def __init__(
        self,
        buffer_cache: LoggerBufferCache,
        buffer_config: LoggerBufferConfig,
        source_logger: Logger,
    ):
        """
        Initialize the BufferingHandler.

        Parameters
        ----------
        buffer_cache : LoggerBufferCache
            Shared buffer cache from the source logger
        buffer_config : LoggerBufferConfig
            Buffer configuration from the source logger
        source_logger : Logger
            The Powertools Logger instance to delegate buffering logic to
        """
        super().__init__()
        self.buffer_cache = buffer_cache
        self.buffer_config = buffer_config
        self.source_logger = source_logger

    def emit(self, record: logging.LogRecord) -> None:
        """
        Buffer or emit the log record based on the buffer verbosity threshold.

        Logs above the configured buffer_at_verbosity are emitted directly
        through the source logger. Logs at or below the threshold are buffered.

        Parameters
        ----------
        record : logging.LogRecord
            The log record from an external logger
        """
        level_name = logging.getLevelName(record.levelno)

        # If log level exceeds buffer threshold, emit directly through source logger
        if _check_minimum_buffer_log_level(self.buffer_config.buffer_at_verbosity, level_name):
            self.source_logger._logger.handle(record)
            return

        self.source_logger._add_log_record_to_buffer(
            level=record.levelno,
            msg=record.msg,
            args=record.args,
            exc_info=record.exc_info,
            stack_info=False,
        )
