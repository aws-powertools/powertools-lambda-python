from __future__ import annotations

from typing import Literal


class LoggerBufferConfig:
    """
    Configuration for log buffering behavior.
    """

    # Define class-level constant for valid log levels
    VALID_LOG_LEVELS: list[str] = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def __init__(
        self,
        max_size: int = 10240,
        minimum_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG",
        flush_on_error: bool = True,
        compress: bool = False,
    ):
        """
        Initialize logger buffer configuration.

        Parameters
        ----------
        max_size : int, optional
            Maximum size of the buffer in bytes
        minimum_log_level : str, optional
            Minimum log level to buffer
        flush_on_error : bool, optional
            Whether to flush the buffer when an error occurs
        compress : bool, optional
            Whether to compress buffered logs
        """
        self._validate_inputs(max_size, minimum_log_level, flush_on_error, compress)

        self._max_size = max_size
        self._minimum_log_level = minimum_log_level.upper()
        self._flush_on_error = flush_on_error
        self._compress = compress

    def _validate_inputs(
        self,
        max_size: int,
        minimum_log_level: str,
        flush_on_error: bool,
        compress: bool,
    ) -> None:
        """
        Validate configuration inputs.

        Parameters
        ----------
        Same as __init__ method parameters
        """
        if not isinstance(max_size, int) or max_size <= 0:
            raise ValueError("Max size must be a positive integer")

        if not isinstance(minimum_log_level, str):
            raise ValueError("Log level must be a string")

        # Validate log level
        if minimum_log_level.upper() not in self.VALID_LOG_LEVELS:
            raise ValueError(f"Invalid log level. Must be one of {self.VALID_LOG_LEVELS}")

        if not isinstance(flush_on_error, bool):
            raise ValueError("flush_on_error must be a boolean")

        if not isinstance(compress, bool):
            raise ValueError("compress must be a boolean")

    @property
    def max_size(self) -> int:
        """Maximum buffer size in bytes."""
        return self._max_size

    @property
    def minimum_log_level(self) -> str:
        """Minimum log level to buffer."""
        return self._minimum_log_level

    @property
    def flush_on_error(self) -> bool:
        """Flag to flush buffer on error."""
        return self._flush_on_error

    @property
    def compress(self) -> bool:
        """Flag to compress buffered logs."""
        return self._compress
