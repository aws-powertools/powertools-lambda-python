from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from collections.abc import Callable


class ResolverTypeDef(TypedDict):
    """
    Type definition for resolver dictionary
    Parameters
    ----------
    func: Callable[..., Any]
        Resolver function
    aggregate: bool
        Aggregation flag or method
    """

    func: Callable[..., Any]
    aggregate: bool
