"""Generics and other shared types used across parser"""

from __future__ import annotations

from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Json

Model = TypeVar("Model", bound=BaseModel)
EnvelopeModel = TypeVar("EnvelopeModel")
EventParserReturnType = TypeVar("EventParserReturnType")
AnyInheritedModel = type[BaseModel] | BaseModel
RawDictOrModel = dict[str, Any] | AnyInheritedModel
T = TypeVar("T")

__all__ = ["Json", "Literal"]
