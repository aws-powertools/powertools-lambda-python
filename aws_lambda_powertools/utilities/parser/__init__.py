"""Advanced event_parser utility"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from aws_lambda_powertools.utilities.parser.parser import event_parser, parse

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser import envelopes as envelopes
    from aws_lambda_powertools.utilities.parser.envelopes import BaseEnvelope


def __getattr__(name: str) -> object:
    if name == "envelopes":
        _envelopes = importlib.import_module(f"{__name__}.envelopes")
        globals()[name] = _envelopes
        return _envelopes
    if name == "BaseEnvelope":
        _envelopes_module = importlib.import_module(f"{__name__}.envelopes")
        _base_envelope = _envelopes_module.BaseEnvelope
        globals()[name] = _base_envelope
        return _base_envelope
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "event_parser",
    "parse",
    "envelopes",
    "BaseEnvelope",
    "BaseModel",
    "Field",
    "field_validator",
    "model_validator",
    "ValidationError",
]
