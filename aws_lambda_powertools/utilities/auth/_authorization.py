from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aws_lambda_powertools.utilities.auth._validation import string_list
from aws_lambda_powertools.utilities.auth.exceptions import AuthError, InvalidClaimsError, InvalidTokenError


class MissingTokenError(InvalidTokenError):
    """No authorization header was supplied."""


class ForbiddenError(AuthError):
    """A verified caller does not have permission for this operation."""


class InsufficientScopeError(ForbiddenError):
    """A verified caller is missing a required scope."""


def bearer_token(value: Any) -> str:
    if value is None:
        raise MissingTokenError()
    if not isinstance(value, str):
        raise InvalidTokenError()
    parts = value.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise InvalidTokenError()
    return parts[1]


def header_token(headers: Any, multi_value_headers: Any = None) -> str:
    values = _authorization_values(headers)
    multi_values = _authorization_values(multi_value_headers)
    if multi_values:
        entries = multi_values[0]
        if not isinstance(entries, list) or len(entries) != 1:
            raise InvalidTokenError()
        if values and values[0] != entries[0]:
            raise InvalidTokenError()
        return bearer_token(entries[0])
    return bearer_token(values[0] if values else None)


def _authorization_values(headers: Any) -> list[Any]:
    if headers is None:
        return []
    if not isinstance(headers, Mapping):
        raise InvalidTokenError()
    values = [value for name, value in headers.items() if isinstance(name, str) and name.lower() == "authorization"]
    if len(values) > 1:
        raise InvalidTokenError()
    return values


def valid_scope(value: str) -> bool:
    return bool(value) and all(33 <= ord(character) <= 126 and character not in {'"', "\\"} for character in value)


def required_scopes(scopes: list[str] | None) -> tuple[str, ...]:
    values = string_list(scopes if scopes is not None else [])
    if not all(valid_scope(value) for value in values):
        raise ValueError("Scopes must be valid OAuth scope tokens")
    return values


def enforce_scopes(claims: dict[str, Any], expected: tuple[str, ...]) -> None:
    value: Any = next((claims[name] for name in ("scope", "scp", "scopes") if name in claims), [])
    if isinstance(value, str):
        values = [part for part in value.split(" ") if part]
    elif isinstance(value, list):
        values = value
    else:
        raise InvalidClaimsError()
    if any(not isinstance(scope, str) or not valid_scope(scope) for scope in values):
        raise InvalidClaimsError()
    if not set(expected).issubset(values):
        raise InsufficientScopeError()
