"""Generics and other shared types used across parser"""

import sys
from typing import Any, Dict, Type, TypeVar, Union

from pydantic import BaseModel, Json

# We only need typing_extensions for python versions <3.8
if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

Model = TypeVar("Model", bound=BaseModel)
EnvelopeModel = TypeVar("EnvelopeModel")
EventParserReturnType = TypeVar("EventParserReturnType")
AnyInheritedModel = Union[Type[BaseModel], BaseModel]
RawDictOrModel = Union[Dict[str, Any], AnyInheritedModel]

__all__ = ["Json", "Literal"]
