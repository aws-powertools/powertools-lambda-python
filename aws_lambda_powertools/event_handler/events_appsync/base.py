from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

DEFAULT_ROUTE = "/default/*"


class BaseRouter(ABC):
    """Abstract base class for Router (resolvers)"""

    @abstractmethod
    def on_publish(
        self,
        path: str = DEFAULT_ROUTE,
        aggregate: bool = True,
    ) -> Callable:
        raise NotImplementedError

    @abstractmethod
    def async_on_publish(
        self,
        path: str = DEFAULT_ROUTE,
        aggregate: bool = True,
    ) -> Callable:
        raise NotImplementedError

    @abstractmethod
    def on_subscribe(
        self,
        path: str = DEFAULT_ROUTE,
    ) -> Callable:
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
