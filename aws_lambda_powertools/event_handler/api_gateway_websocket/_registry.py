from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING

from aws_lambda_powertools.event_handler.api_gateway_websocket.types import WebSocketRoute
from aws_lambda_powertools.warnings import PowertoolsUserWarning

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class RouteRegistry:
    def __init__(self):
        self.routes: dict[str, WebSocketRoute] = {}

    def register(
        self,
        route_key: str,
        middlewares: list[Callable] | None = None,
    ) -> Callable:
        """Registers a route handler for a route key

        Parameters
        ----------
        route_key : str
            Route key produced by the API's route selection expression, e.g. `$connect` or a custom key
        middlewares : list[Callable] | None
            Middlewares to run around the handler for this route

        Return
        ----------
        Callable
            A decorator that registers the handler
        """

        def _register(func: Callable) -> Callable:
            if not route_key:
                warnings.warn(
                    f"The route key registered for `{getattr(func, '__name__', func)}` is empty and will be skipped.",
                    stacklevel=2,
                    category=PowertoolsUserWarning,
                )
                return func

            if route_key in self.routes:
                warnings.warn(
                    f"A route handler is already registered for route key `{route_key}`. "
                    "The last registration will be used.",
                    stacklevel=2,
                    category=PowertoolsUserWarning,
                )

            logger.debug(f"Adding route handler `{func.__name__}` for route key `{route_key}`")
            self.routes[route_key] = WebSocketRoute(func=func, middlewares=middlewares or [])
            return func

        return _register

    def find_route(self, route_key: str) -> WebSocketRoute | None:
        """Find a route handler by exact route key match

        Parameters
        ----------
        route_key : str
            Route key to look up

        Return
        ----------
        WebSocketRoute | None
            The registered route, or None when no handler is registered for the route key
        """
        logger.debug(f"Looking for route handler for route key `{route_key}`")
        return self.routes.get(route_key)

    def merge(self, other_registry: RouteRegistry) -> None:
        """Update current registry with routes from an incoming registry

        Parameters
        ----------
        other_registry : RouteRegistry
            Registry to merge from
        """
        self.routes.update(**other_registry.routes)
