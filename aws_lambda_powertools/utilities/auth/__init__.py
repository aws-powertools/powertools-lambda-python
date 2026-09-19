"""JWT access-token verification for AWS Lambda."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.auth._middleware import AuthErrorContext as AuthErrorContext
    from aws_lambda_powertools.utilities.auth.exceptions import AuthFailureReason as AuthFailureReason
    from aws_lambda_powertools.utilities.auth.verifier import JWTVerifier as JWTVerifier

__all__ = ["AuthErrorContext", "AuthFailureReason", "JWTVerifier"]


def __getattr__(name: str) -> object:
    modules = {"AuthErrorContext": "_middleware", "AuthFailureReason": "exceptions", "JWTVerifier": "verifier"}
    if name in modules:
        value = getattr(importlib.import_module(f"{__name__}.{modules[name]}"), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
