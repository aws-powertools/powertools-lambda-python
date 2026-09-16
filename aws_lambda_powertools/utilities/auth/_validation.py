from __future__ import annotations

import math
from typing import Any
from urllib.parse import urlsplit


def https_url(value: str, *, issuer: bool = False) -> str:
    """Validate configured URLs without echoing their contents in errors."""
    try:
        parts = urlsplit(value)
        valid = isinstance(value, str) and all(
            (
                _valid_url_characters(value),
                parts.scheme == "https",
                bool(parts.hostname),
                parts.username is None,
                parts.password is None,
                not parts.fragment,
                not issuer or not parts.query,
            ),
        )
        _ = parts.port  # Accessing the property validates a supplied port.
    except (AttributeError, TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError("An HTTPS URL without user information or a fragment is required") from None
    return value


def _valid_url_characters(value: str) -> bool:
    return not any(character.isspace() or ord(character) < 32 for character in value)


def finite_seconds(value: float, *, positive: bool = False) -> float:
    """Validate a duration; booleans and non-finite values are not durations."""
    try:
        valid = type(value) in (int, float) and math.isfinite(value) and value >= 0 and (not positive or value > 0)
    except OverflowError:
        valid = False
    if not valid:
        message = "A finite positive duration is required" if positive else "A finite nonnegative duration is required"
        raise ValueError(message)
    return value


def string_list(values: list[str] | tuple[str, ...], *, nonempty: bool = False) -> tuple[str, ...]:
    """Copy a sequence of nonempty strings so configuration cannot be mutated."""
    if not isinstance(values, (list, tuple)) or (nonempty and not values):
        raise ValueError("A list of nonempty strings is required")
    if not all(is_nonempty_string(value) for value in values):
        raise ValueError("A list of nonempty strings is required")
    return tuple(dict.fromkeys(values))


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
