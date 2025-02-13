from __future__ import annotations

import inspect
import time
from typing import Any, Mapping


def _create_buffer_record(
    level: int,
    msg: object,
    args: object,
    extra: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    caller_frame = inspect.stack()[2]
    timestamp = time.time()

    return {
        "level": level,
        "msg": msg,
        "args": args,
        "filename": caller_frame.filename,
        "line": caller_frame.lineno,
        "function": caller_frame.function,
        "extra": extra,
        "timestamp": timestamp,
    }


def _check_minimum_buffer_log_level(buffer_log_level, current_log_level):
    # Define log level mapping
    log_levels = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    }

    # Convert string levels to numeric if needed
    buffer_level_num = log_levels.get(buffer_log_level.upper())
    current_level_num = log_levels.get(current_log_level.upper())

    # Compare numeric levels
    if buffer_level_num < current_level_num:
        return True

    return False
