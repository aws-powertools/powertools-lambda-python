"""Advanced event_parser utility"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from aws_lambda_powertools.utilities.parser.parser import event_parser, parse

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parser import envelopes as envelopes
    from aws_lambda_powertools.utilities.parser.envelopes import BaseEnvelope


def __getattr__(name: str) -> object:
    if name == "envelopes":
        from aws_lambda_powertools.utilities.parser import envelopes as _envelopes  # noqa: PLC0415

        return _envelopes
    if name == "BaseEnvelope":
        from aws_lambda_powertools.utilities.parser.envelopes import BaseEnvelope as _BaseEnvelope  # noqa: PLC0415

        return _BaseEnvelope
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
