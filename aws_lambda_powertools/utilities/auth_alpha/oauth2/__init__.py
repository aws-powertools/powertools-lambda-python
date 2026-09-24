"""OAuth 2.0 client-credentials token acquisition."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.auth_alpha.oauth2.client import OAuth2Client as OAuth2Client

__all__ = ["OAuth2Client"]


def __getattr__(name: str) -> object:
    if name == "OAuth2Client":
        value = importlib.import_module(f"{__name__}.client").OAuth2Client
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
