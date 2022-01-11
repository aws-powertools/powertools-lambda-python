from typing import Any, Callable, Dict, List, TypeVar, Union

AnyCallableT = TypeVar("AnyCallableT", bound=Callable[..., Any])  # noqa: VNE001
# JSON primitives only, mypy doesn't support recursive tho
JSONType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
