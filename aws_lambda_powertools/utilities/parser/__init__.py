"""Advanced event_parser utility
"""

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from aws_lambda_powertools.utilities.parser import envelopes
from aws_lambda_powertools.utilities.parser.envelopes import BaseEnvelope
from aws_lambda_powertools.utilities.parser.parser import event_parser, parse

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
