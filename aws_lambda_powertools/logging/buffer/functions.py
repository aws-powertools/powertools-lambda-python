from __future__ import annotations

import sys
import time
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    import logging


def _create_buffer_record(
    level: int,
    msg: object,
    args: object,
    exc_info: logging._ExcInfoType = None,
    stack_info: bool = False,
    extra: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    """
    Create a structured log record for buffering to save in buffer.

    Parameters
    ----------
    level : int
        Logging level (e.g., logging.DEBUG, logging.INFO) indicating log severity.
    msg : object
        The log message to be recorded.
    args : object
        Additional arguments associated with the log message.
    exc_info : logging._ExcInfoType, optional
        Exception information to be included in the log record.
        If None, no exception details will be captured.
    stack_info : bool, default False
        Flag to include stack trace information in the log record.
    extra : Mapping[str, object], optional
        Additional context or metadata to be attached to the log record.

    Returns
    -------
    dict[str, Any]

    Notes
    -----
    - Captures caller frame information for precise log source tracking
    - Automatically handles exception context
    """
    # Retrieve the caller's frame information to capture precise log context
    # Uses inspect.stack() with index 3 to get the original caller's details
    caller_frame = sys._getframe(3)

    # Get the current timestamp
    timestamp = time.time()

    # Dynamically replace exc_info with current system exception information
    # This ensures the most recent exception is captured if available
    if exc_info:
        exc_info = sys.exc_info()

    # Construct and return the og record dictionary
    return {
        "level": level,
        "msg": msg,
        "args": args,
        "filename": caller_frame.f_code.co_filename,
        "line": caller_frame.f_lineno,
        "function": caller_frame.f_code.co_name,
        "extra": extra,
        "timestamp": timestamp,
        "exc_info": exc_info,
        "stack_info": stack_info,
    }


def _check_minimum_buffer_log_level(buffer_log_level, current_log_level):
    """
    Determine if the current log level meets or exceeds the buffer's minimum log level.

    Compares log levels to decide whether a log message should be included in the buffer.

    Parameters
    ----------
    buffer_log_level : str
        Minimum log level configured for the buffer.
        Must be one of: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.
    current_log_level : str
        Log level of the current log message.
        Must be one of: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.

    Returns
    -------
    bool
        True if the current log level is lower (more verbose) than the buffer's
        minimum log level, indicating the message should be buffered.
        False if the current log level is higher (less verbose) and should not be buffered.

    Notes
    -----
    - Log levels are compared based on their numeric severity
    - Conversion to uppercase ensures case-insensitive comparisons

    Examples
    --------
    >>> _check_minimum_buffer_log_level('INFO', 'DEBUG')
    True
    >>> _check_minimum_buffer_log_level('ERROR', 'WARNING')
    False
    """
    # Predefined log level mapping with numeric severity values
    # Lower values indicate more verbose logging levels
    log_levels = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    }

    # Normalize input log levels to uppercase for consistent comparison
    # Retrieve corresponding numeric log level values
    buffer_level_num = log_levels.get(buffer_log_level.upper())
    current_level_num = log_levels.get(current_log_level.upper())

    # Compare numeric levels
    if buffer_level_num < current_level_num:
        return True

    return False
