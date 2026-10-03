from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from collections.abc import Callable


class WebSocketRoute(TypedDict):
    """
    Type definition for a registered WebSocket route

    Parameters
    ----------
    func: Callable[..., Any]
        Route handler function
    middlewares: list[Callable[..., Any]]
        Middlewares to run around the handler for this route
    """

    func: Callable[..., Any]
    middlewares: list[Callable[..., Any]]
