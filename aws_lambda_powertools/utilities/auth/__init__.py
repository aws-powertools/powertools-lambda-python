"""JWT verification and OAuth2 client credentials for AWS Lambda."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.auth.oauth2 import OAuth2Client as OAuth2Client
    from aws_lambda_powertools.utilities.auth.verifier import JWTVerifier as JWTVerifier

__all__ = ["JWTVerifier", "OAuth2Client"]


def __getattr__(name: str) -> object:
    modules = {"JWTVerifier": "verifier", "OAuth2Client": "oauth2"}
    if name in modules:
        value = getattr(importlib.import_module(f"{__name__}.{modules[name]}"), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
