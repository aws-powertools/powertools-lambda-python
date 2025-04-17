from __future__ import annotations

import types
from typing import TYPE_CHECKING, Any, Dict, Set, Type, TypedDict, Union

if TYPE_CHECKING:
    from collections.abc import Callable
    from enum import Enum

    from pydantic import BaseModel
    from typing_extensions import NotRequired

    CacheKey = Union[Callable[..., Any], None]
    IncEx = Union[Set[int], Set[str], Dict[int, Any], Dict[str, Any]]
    TypeModelOrEnum = Union[Type[BaseModel], Type[Enum]]
    ModelNameMap = Dict[TypeModelOrEnum, str]

UnionType = getattr(types, "UnionType", Union)


COMPONENT_REF_PREFIX = "#/components/schemas/"
COMPONENT_REF_TEMPLATE = "#/components/schemas/{model}"
METHODS_WITH_BODY = {"GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"}


validation_error_definition = {
    "title": "ValidationError",
    "type": "object",
    "properties": {
        "loc": {
            "title": "Location",
            "type": "array",
            "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
        },
        # For security reasons, we hide **msg** details (don't leak Python, Pydantic or filenames)
        "type": {"title": "Error Type", "type": "string"},
    },
    "required": ["loc", "msg", "type"],
}

validation_error_response_definition = {
    "title": "HTTPValidationError",
    "type": "object",
    "properties": {
        "detail": {
            "title": "Detail",
            "type": "array",
            "items": {"$ref": f"{COMPONENT_REF_PREFIX}ValidationError"},
        },
    },
}

response_validation_error_response_definition = {
    "title": "ResponseValidationError",
    "type": "object",
    "properties": {
        "detail": {
            "title": "Detail",
            "type": "array",
            "items": {"$ref": f"{COMPONENT_REF_PREFIX}ValidationError"},
        },
    },
}


class OpenAPIResponseContentSchema(TypedDict, total=False):
    schema: dict


class OpenAPIResponseContentModel(TypedDict):
    model: Any


class OpenAPIResponse(TypedDict):
    description: str
    content: NotRequired[dict[str, OpenAPIResponseContentSchema | OpenAPIResponseContentModel]]
