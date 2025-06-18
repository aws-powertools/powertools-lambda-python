from __future__ import annotations

import sys
from dataclasses import is_dataclass
from typing import TYPE_CHECKING, Annotated, Any, Optional, Union, get_args, get_origin

# Conditionally import or define UnionType based on Python version
if sys.version_info >= (3, 10):
    from types import UnionType  # Available in Python 3.10+
else:
    UnionType = Union  # Fallback for Python 3.9

from aws_lambda_powertools.utilities.kafka.serialization.custom_dict import CustomDictOutputSerializer
from aws_lambda_powertools.utilities.kafka.serialization.dataclass import DataclassOutputSerializer

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.kafka.serialization.types import T


def _get_output_serializer(output: type[T] | Callable | None = None) -> Any:
    """
    Returns the appropriate serializer for the given output class.
    Uses lazy imports to avoid unnecessary dependencies.
    """
    # Check if it's a dataclass
    if is_dataclass(output):
        return DataclassOutputSerializer()

    if _is_pydantic_model(output):
        from aws_lambda_powertools.utilities.kafka.serialization.pydantic import PydanticOutputSerializer

        return PydanticOutputSerializer()

    # Default to custom serializer
    return CustomDictOutputSerializer()


def _is_pydantic_model(obj: Any) -> bool:
    if isinstance(obj, type):
        # Check for Pydantic model attributes without direct import
        has_model_fields = getattr(obj, "model_fields", None) is not None
        has_model_validate = callable(getattr(obj, "model_validate", None))
        return has_model_fields and has_model_validate

    origin = get_origin(obj)
    if origin in (Union, Optional, Annotated) or (sys.version_info >= (3, 10) and origin in (Union, UnionType)):
        # Check if any element in the Union is a Pydantic model
        for arg in get_args(obj):
            if _is_pydantic_model(arg):
                return True

    return False


def serialize_to_output_type(
    data: object | dict[str, Any],
    output: type[T] | Callable | None = None,
) -> T | dict[str, Any]:
    """
    Helper function to directly serialize data to the specified output class
    """
    serializer = _get_output_serializer(output)
    return serializer.serialize(data, output)
