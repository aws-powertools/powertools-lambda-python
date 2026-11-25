from __future__ import annotations

import io
import sys
import time
import traceback
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import logging
    from collections.abc import Mapping
    from types import FrameType


def _get_caller_frame(stacklevel: int) -> FrameType:
    """
    Walk up the stack from _create_buffer_record's caller, honouring stacklevel.

    The walk starts at _add_log_record_to_buffer and counts user frames above
    the logging call, mirroring logging.Logger.findCaller: the default
    stacklevel of 2 reports the direct caller of the Powertools log method,
    and each extra level reports one more caller up the stack. Stops at the
    outermost frame if stacklevel walks past the top of the stack.
    """
    frame = sys._getframe(2)  # _add_log_record_to_buffer
    for _ in range(stacklevel):
        next_frame = frame.f_back
        if next_frame is None:
            break
        frame = next_frame
    return frame


def _format_stack(frame: FrameType) -> str:
    """
    Format the stack starting at frame, the same way logging.Logger.findCaller does.
    """
    with io.StringIO() as sio:
        sio.write("Stack (most recent call last):\n")
        traceback.print_stack(frame, file=sio)
        stack = sio.getvalue()
        return stack[:-1] if stack.endswith("\n") else stack


def _create_buffer_record(
    level: int,
    msg: object,
    args: object,
    exc_info: logging._ExcInfoType = None,
    stack_info: bool = False,
    extra: Mapping[str, object] | None = None,
    stacklevel: int = 2,
    pathname: str | None = None,
    lineno: int | None = None,
    func_name: str | None = None,
    logger_name: str | None = None,
    sinfo: str | None = None,
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
        Only True is resolved to the current exception; a tuple or an
        exception instance passed by the caller is kept as-is.
    stack_info : bool, default False
        Flag to include stack trace information in the log record.
    extra : Mapping[str, object], optional
        Additional context or metadata to be attached to the log record.
    stacklevel : int, default 2
        Number of user frames above the logging call to report as the
        record's location. The default reports the direct caller.
    pathname : str, optional
        Source filename of the record. Resolved from the caller frame
        honouring stacklevel when not provided.
    lineno : int, optional
        Source line number of the record. Resolved from the caller frame
        honouring stacklevel when not provided.
    func_name : str, optional
        Source function name of the record. Resolved from the caller frame
        honouring stacklevel when not provided.
    logger_name : str, optional
        Name of the logger the record came from. Records from third-party
        loggers carry their own logger name.
    sinfo : str, optional
        Pre-formatted stack information. Computed from the caller frame
        when stack_info is True and no sinfo is provided.

    Returns
    -------
    dict[str, Any]

    Notes
    -----
    - Captures caller frame information for precise log source tracking
    - Automatically handles exception context
    """
    # Records from third-party loggers arrive with their origin already known;
    # use it as-is instead of resolving a frame from inside the logging internals.
    if pathname is None and lineno is None and func_name is None:
        caller_frame = _get_caller_frame(stacklevel)
        pathname = caller_frame.f_code.co_filename
        lineno = caller_frame.f_lineno
        func_name = caller_frame.f_code.co_name

        if stack_info and sinfo is None:
            sinfo = _format_stack(caller_frame)

    # Get the current timestamp
    timestamp = time.time()

    # Only True resolves to the current exception, mirroring logging.Logger._log.
    # A tuple or an exception instance passed by the caller is kept as-is,
    # so an exception saved outside its except block still flushes with it.
    if exc_info is True:
        exc_info = sys.exc_info()
    elif isinstance(exc_info, BaseException):
        exc_info = (type(exc_info), exc_info, exc_info.__traceback__)

    # Construct and return the log record dictionary
    return {
        "level": level,
        "msg": msg,
        "args": args,
        "pathname": pathname,
        "lineno": lineno,
        "funcName": func_name,
        "name": logger_name,
        "extra": extra,
        "timestamp": timestamp,
        "exc_info": exc_info,
        "stack_info": stack_info,
        "sinfo": sinfo,
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

    if buffer_level_num is None or current_level_num is None:
        return False

    # Compare numeric levels
    if buffer_level_num < current_level_num:
        return True

    return False
