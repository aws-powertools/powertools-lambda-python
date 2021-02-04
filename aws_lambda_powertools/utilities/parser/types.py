"""Generics and other shared types used across parser"""

from typing import TypeVar

from pydantic import BaseModel

# We only need typing_extensions for python versions <3.8
try:
    from typing import Literal  # noqa: F401
except ImportError:
    from typing_extensions import Literal  # noqa: F401

Model = TypeVar("Model", bound=BaseModel)
