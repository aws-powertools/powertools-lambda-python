from typing import Any, Dict, List, Union

# JSON primitives only, mypy doesn't support recursive tho
JSONType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
