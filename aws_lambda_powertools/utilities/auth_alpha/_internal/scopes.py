from __future__ import annotations

from aws_lambda_powertools.utilities.auth_alpha._internal.validation import string_list


def valid_scope(value: str) -> bool:
    return bool(value) and all(33 <= ord(character) <= 126 and character not in {'"', "\\"} for character in value)


def required_scopes(scopes: list[str] | None) -> tuple[str, ...]:
    values = string_list(scopes if scopes is not None else [])
    if not all(valid_scope(value) for value in values):
        raise ValueError("Scopes must be valid OAuth scope tokens")
    return values
