"""Generics and other shared types used across parser"""
from typing import TypeVar

from pydantic import BaseModel

Model = TypeVar("Model", bound=BaseModel)
