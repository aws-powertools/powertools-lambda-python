"""Generics and other shared types used across parser"""

from typing import Any, Dict, Literal, Type, TypeVar, Union

from pydantic import BaseModel, Json

Model = TypeVar("Model", bound=BaseModel)
EnvelopeModel = TypeVar("EnvelopeModel")
EventParserReturnType = TypeVar("EventParserReturnType")
AnyInheritedModel = Union[Type[BaseModel], BaseModel]
RawDictOrModel = Union[Dict[str, Any], AnyInheritedModel]
T = TypeVar("T")

__all__ = ["Json", "Literal"]
