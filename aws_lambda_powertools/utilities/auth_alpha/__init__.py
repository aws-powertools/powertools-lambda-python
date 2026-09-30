"""Alpha authentication and authorization utilities for AWS Lambda."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.auth_alpha.exceptions import AuthFailureReason as AuthFailureReason
    from aws_lambda_powertools.utilities.auth_alpha.jwt import AuthErrorContext as AuthErrorContext
    from aws_lambda_powertools.utilities.auth_alpha.jwt import JWTVerifier as JWTVerifier
    from aws_lambda_powertools.utilities.auth_alpha.oauth2 import OAuth2Client as OAuth2Client

__all__ = ["AuthErrorContext", "AuthFailureReason", "JWTVerifier", "OAuth2Client"]


def __getattr__(name: str) -> object:
    modules = {
        "AuthErrorContext": "jwt",
        "AuthFailureReason": "exceptions",
        "JWTVerifier": "jwt",
        "OAuth2Client": "oauth2",
    }
    if name in modules:
        value = getattr(importlib.import_module(f"{__name__}.{modules[name]}"), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
