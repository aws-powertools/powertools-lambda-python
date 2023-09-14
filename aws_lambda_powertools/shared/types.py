import sys
from typing import Any, Callable, Dict, List, TypeVar, Union

if sys.version_info >= (3, 8):
    from typing import Literal, Protocol, TypedDict
else:
    from typing_extensions import Literal, Protocol, TypedDict


if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired


if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

AnyCallableT = TypeVar("AnyCallableT", bound=Callable[..., Any])  # noqa: VNE001
# JSON primitives only, mypy doesn't support recursive tho
JSONType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]

__all__ = ["Protocol", "TypedDict", "Literal", "NotRequired", "TypeAlias"]
