"""Generics and other shared types used across parser"""

import sys
from typing import TypeVar

from pydantic import BaseModel

# We only need typing_extensions for python versions <3.8
if sys.version_info >= (3, 8):
    from typing import Literal  # noqa: F401
else:
    from typing_extensions import Literal  # noqa: F401

Model = TypeVar("Model", bound=BaseModel)
EnvelopeModel = TypeVar("EnvelopeModel")
EventParserReturnType = TypeVar("EventParserReturnType")
