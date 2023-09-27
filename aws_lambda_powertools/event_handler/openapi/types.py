from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Set, Type, Union

from pydantic.version import VERSION as PYDANTIC_VERSION

if TYPE_CHECKING:
    from pydantic import BaseModel  # noqa: F401

CacheKey = Optional[Callable[..., Any]]
IncEx = Union[Set[int], Set[str], Dict[int, Any], Dict[str, Any]]
ModelNameMap = Dict[Union[Type["BaseModel"], Type[Enum]], str]
TypeModelOrEnum = Union[Type["BaseModel"], Type[Enum]]

PYDANTIC_V2 = PYDANTIC_VERSION.startswith("2.")
COMPONENT_REF_PREFIX = "#/components/schemas/"
COMPONENT_REF_TEMPLATE = "#/components/schemas/{model}"
