import sys
from typing import Any, Callable, Dict, List, Literal, Protocol, TypedDict, TypeVar, Union

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired

# Even though `get_args` and `get_origin` were added in Python 3.8, they only handle Annotated correctly on 3.10.
# So for python < 3.10 we use the backport from typing_extensions.
if sys.version_info >= (3, 10):
    from typing import TypeAlias, get_args, get_origin
else:
    from typing_extensions import TypeAlias, get_args, get_origin

AnyCallableT = TypeVar("AnyCallableT", bound=Callable[..., Any])  # noqa: VNE001


# JSON primitives only, mypy doesn't support recursive tho
JSONType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]

__all__ = ["get_args", "get_origin", "Annotated", "Protocol", "TypedDict", "Literal", "NotRequired", "TypeAlias"]
