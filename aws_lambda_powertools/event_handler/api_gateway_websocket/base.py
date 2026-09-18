from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

ROUTE_KEY_CONNECT = "$connect"
ROUTE_KEY_DISCONNECT = "$disconnect"
ROUTE_KEY_DEFAULT = "$default"


class BaseRouter(ABC):
    """Abstract base class for WebSocket routers (resolvers)"""

    @abstractmethod
    def route(
        self,
        route_key: str,
        middlewares: list[Callable] | None = None,
    ) -> Callable:
        raise NotImplementedError

    @abstractmethod
    def on_connect(
        self,
        middlewares: list[Callable] | None = None,
    ) -> Callable:
        raise NotImplementedError

    @abstractmethod
    def on_disconnect(
        self,
        middlewares: list[Callable] | None = None,
    ) -> Callable:
        raise NotImplementedError

    @abstractmethod
    def on_default(
        self,
        middlewares: list[Callable] | None = None,
    ) -> Callable:
        raise NotImplementedError

    @abstractmethod
    def use(self, middlewares: list[Callable]) -> None:
        raise NotImplementedError

    def append_context(self, **additional_context) -> None:
        """
        Appends context information available under any route.

        Parameters
        -----------
        **additional_context: dict
            Additional context key-value pairs to append.
        """
        raise NotImplementedError
