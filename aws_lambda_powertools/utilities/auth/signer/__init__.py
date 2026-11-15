"""AWS Signature Version 4 and 4A request signing."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.auth.signer.sigv4 import SignedRequest as SignedRequest
    from aws_lambda_powertools.utilities.auth.signer.sigv4 import SigV4Signer as SigV4Signer
    from aws_lambda_powertools.utilities.auth.signer.sigv4a import SigV4aSigner as SigV4aSigner

__all__ = ["SigV4Signer", "SigV4aSigner", "SignedRequest"]


def __getattr__(name: str) -> object:
    modules = {"SigV4Signer": "sigv4", "SignedRequest": "sigv4", "SigV4aSigner": "sigv4a"}
    if name in modules:
        value = getattr(importlib.import_module(f"{__name__}.{modules[name]}"), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
