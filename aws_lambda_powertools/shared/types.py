from collections.abc import Callable
from typing import Any, Protocol, TypeVar

AnyCallableT = TypeVar("AnyCallableT", bound=Callable[..., Any])

EventT_contra = TypeVar("EventT_contra", contravariant=True)
ContextT_contra = TypeVar("ContextT_contra", contravariant=True)
ReturnT_co = TypeVar("ReturnT_co", covariant=True)


class LambdaHandler(Protocol[EventT_contra, ContextT_contra, ReturnT_co]):
    """Lambda handler, callable with `event` and `context` as positional or keyword arguments."""

    def __call__(self, event: EventT_contra, context: ContextT_contra) -> ReturnT_co: ...
