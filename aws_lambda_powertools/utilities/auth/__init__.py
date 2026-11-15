"""Authentication and authorization utilities for AWS Lambda."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.auth.exceptions import AuthFailureReason as AuthFailureReason
    from aws_lambda_powertools.utilities.auth.jwt import AuthErrorContext as AuthErrorContext
    from aws_lambda_powertools.utilities.auth.jwt import JWTVerifier as JWTVerifier
    from aws_lambda_powertools.utilities.auth.oauth2 import OAuth2Client as OAuth2Client
    from aws_lambda_powertools.utilities.auth.signer import SignedRequest as SignedRequest
    from aws_lambda_powertools.utilities.auth.signer import SigV4aSigner as SigV4aSigner
    from aws_lambda_powertools.utilities.auth.signer import SigV4Signer as SigV4Signer

__all__ = [
    "AuthErrorContext",
    "AuthFailureReason",
    "JWTVerifier",
    "OAuth2Client",
    "SigV4Signer",
    "SigV4aSigner",
    "SignedRequest",
]


def __getattr__(name: str) -> object:
    modules = {
        "AuthErrorContext": "jwt",
        "AuthFailureReason": "exceptions",
        "JWTVerifier": "jwt",
        "OAuth2Client": "oauth2",
        "SigV4Signer": "signer",
        "SigV4aSigner": "signer",
        "SignedRequest": "signer",
    }
    if name in modules:
        value = getattr(importlib.import_module(f"{__name__}.{modules[name]}"), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
