from typing import Any, Callable, TypeVar

AnyCallableT = TypeVar("AnyCallableT", bound=Callable[..., Any])  # noqa: VNE001
