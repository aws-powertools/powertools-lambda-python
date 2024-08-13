from __future__ import annotations

from typing import Any

# JSON primitives only, mypy doesn't support recursive tho
JSONType = str | int | float | bool | None | dict[str, Any] | list[Any]
