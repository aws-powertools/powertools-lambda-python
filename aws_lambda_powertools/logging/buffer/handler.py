from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_powertools.logging.buffer.cache import LoggerBufferCache
    from aws_lambda_powertools.logging.buffer.config import LoggerBufferConfig
    from aws_lambda_powertools.logging.logger import Logger


class BufferingHandler(logging.Handler):
    """
    Handler that buffers logs from external libraries using the source logger's buffer.

    The handler intercepts log records from external libraries and
    stores them in the source logger's buffer using the same tracer_id mechanism.
    Logs are flushed when an error occurs or when explicitly requested.
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
        Buffer the log record by delegating to source logger's buffering logic.
        Call source logger to add a structured record to the buffer.

        Parameters
        ----------
        record : logging.LogRecord
            The log record from an external logger
        """
        self.source_logger._add_log_record_to_buffer(
            level=record.levelno,
            msg=record.getMessage(),
            args=(),
            exc_info=record.exc_info,
            stack_info=False,
        )
