from __future__ import annotations

from typing import Literal


class LoggerBufferConfig:
    """
    Configuration for log buffering behavior.
    """

    # Define class-level constant for valid log levels
    VALID_LOG_LEVELS: list[str] = ["DEBUG", "INFO", "WARNING"]
    LOG_LEVEL_BUFFER_VALUES = Literal["DEBUG", "INFO", "WARNING"]

    def __init__(
        self,
        max_bytes: int = 20480,
        buffer_at_verbosity: LOG_LEVEL_BUFFER_VALUES = "DEBUG",
        flush_on_error_log: bool = True,
    ):
        """
        Initialize logger buffer configuration.

        Parameters
        ----------
        max_bytes : int, optional
            Maximum size of the buffer in bytes
        buffer_at_verbosity : str, optional
            Minimum log level to buffer
        flush_on_error_log : bool, optional
            Whether to flush the buffer when an error occurs
        """
        self._validate_inputs(max_bytes, buffer_at_verbosity, flush_on_error_log)

        self._max_bytes = max_bytes
        self._buffer_at_verbosity = buffer_at_verbosity.upper()
        self._flush_on_error_log = flush_on_error_log

    def _validate_inputs(
        self,
        max_bytes: int,
        buffer_at_verbosity: str,
        flush_on_error_log: bool,
    ) -> None:
        """
        Validate configuration inputs.

        Parameters
        ----------
        Same as __init__ method parameters
        """
        if not isinstance(max_bytes, int) or max_bytes <= 0:
            raise ValueError("Max size must be a positive integer")

        if not isinstance(buffer_at_verbosity, str):
            raise ValueError("Log level must be a string")

        # Validate log level
        if buffer_at_verbosity.upper() not in self.VALID_LOG_LEVELS:
            raise ValueError(f"Invalid log level. Must be one of {self.VALID_LOG_LEVELS}")

        if not isinstance(flush_on_error_log, bool):
            raise ValueError("flush_on_error must be a boolean")

    @property
    def max_bytes(self) -> int:
        """Maximum buffer size in bytes."""
        return self._max_bytes

    @property
    def buffer_at_verbosity(self) -> str:
        """Minimum log level to buffer."""
        return self._buffer_at_verbosity

    @property
    def flush_on_error_log(self) -> bool:
        """Flag to flush buffer on error."""
        return self._flush_on_error_log
