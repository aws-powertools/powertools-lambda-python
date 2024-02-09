"""Generics and other shared types used across parser"""

from typing import Any, Dict, Type, TypeVar, Union

from pydantic import BaseModel, Json

from aws_lambda_powertools.shared.types import Literal

Model = TypeVar("Model", bound=BaseModel)
EnvelopeModel = TypeVar("EnvelopeModel")
EventParserReturnType = TypeVar("EventParserReturnType")
AnyInheritedModel = Union[Type[BaseModel], BaseModel]
RawDictOrModel = Union[Dict[str, Any], AnyInheritedModel]

__all__ = ["Json", "Literal"]
