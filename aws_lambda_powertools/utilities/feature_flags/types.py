from typing import Any, Dict, List, TypeVar, Union

from typing_extensions import ParamSpec

# JSON primitives only, mypy doesn't support recursive tho
JSONType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
T = TypeVar("T")
P = ParamSpec("P")
