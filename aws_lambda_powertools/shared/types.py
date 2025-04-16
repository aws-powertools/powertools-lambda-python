from collections.abc import Callable
from typing import Any, TypeVar

AnyCallableT = TypeVar("AnyCallableT", bound=Callable[..., Any])
