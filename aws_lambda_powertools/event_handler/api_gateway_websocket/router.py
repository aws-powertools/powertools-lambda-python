from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.event_handler.api_gateway_websocket._registry import RouteRegistry
from aws_lambda_powertools.event_handler.api_gateway_websocket.base import (
    ROUTE_KEY_CONNECT,
    ROUTE_KEY_DEFAULT,
    ROUTE_KEY_DISCONNECT,
    BaseRouter,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.data_classes.api_gateway_websocket_event import APIGatewayWebSocketEvent
    from aws_lambda_powertools.utilities.typing.lambda_context import LambdaContext


class Router(BaseRouter):
    """
    Router for API Gateway WebSocket API event handling.

    Registers route handlers for WebSocket route keys so they can be split across
    files and later included in an `APIGatewayWebSocketResolver` via `include_router`.

    Attributes
    ----------
    context : dict
        Dictionary to store context information accessible across route handlers
    current_event : APIGatewayWebSocketEvent
        Current event being processed
    lambda_context : LambdaContext
        Lambda context from the AWS Lambda function

    Examples
    --------
    Create a router and define route handlers:

    >>> from aws_lambda_powertools.event_handler.api_gateway_websocket import Router
    >>>
    >>> orders_router = Router()
    >>>
    >>> @orders_router.route("orderUpdate")
    >>> def order_update():
    >>>     order = orders_router.current_event.json_body
    >>>     return {"orderId": order["id"], "status": "updated"}
    """

    context: dict
    current_event: APIGatewayWebSocketEvent
    lambda_context: LambdaContext

    def __init__(self):
        self.context = {}  # early init as customers might add context before event resolution
        self._route_registry = RouteRegistry()
        self._exception_handlers: dict[type[Exception], Callable] = {}
        self._router_middlewares: list[Callable] = []

    def route(
        self,
        route_key: str,
        middlewares: list[Callable] | None = None,
    ) -> Callable:
        """
        Register a handler for a WebSocket route key.

        Route keys are matched exactly against the key selected by the API's
        route selection expression — there is no pattern matching.

        Parameters
        ----------
        route_key : str
            The route key to register the handler for, e.g. `$connect`, `$disconnect`,
            `$default`, or a custom route key such as `orderUpdate`
        middlewares : list[Callable], optional
            Middlewares to run around the handler for this route

        Returns
        -------
        Callable
            Decorator function that registers the route handler

        Examples
        --------
        >>> from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
        >>>
        >>> app = APIGatewayWebSocketResolver()
        >>>
        >>> @app.route("orderUpdate")
        >>> def order_update():
        >>>     return {"received": app.current_event.json_body["id"]}
        """
        return self._route_registry.register(route_key=route_key, middlewares=middlewares)

    def on_connect(
        self,
        middlewares: list[Callable] | None = None,
    ) -> Callable:
        """
        Register a handler for the `$connect` route key.

        The returned status code decides whether API Gateway accepts the connection:
        2xx accepts the WebSocket upgrade, anything else rejects it.

        Parameters
        ----------
        middlewares : list[Callable], optional
            Middlewares to run around the handler for this route

        Returns
        -------
        Callable
            Decorator function that registers the connect handler

        Examples
        --------
        >>> from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
        >>>
        >>> app = APIGatewayWebSocketResolver()
        >>>
        >>> @app.on_connect()
        >>> def connect():
        >>>     connection_id = app.current_event.request_context.connection_id
        >>>     return None  # 200: accept the connection
        """
        return self.route(route_key=ROUTE_KEY_CONNECT, middlewares=middlewares)

    def on_disconnect(
        self,
        middlewares: list[Callable] | None = None,
    ) -> Callable:
        """
        Register a handler for the `$disconnect` route key.

        This handler is invoked on a best-effort basis when the connection closes,
        including for connections whose `$connect` was rejected.

        Parameters
        ----------
        middlewares : list[Callable], optional
            Middlewares to run around the handler for this route

        Returns
        -------
        Callable
            Decorator function that registers the disconnect handler

        Examples
        --------
        >>> from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
        >>>
        >>> app = APIGatewayWebSocketResolver()
        >>>
        >>> @app.on_disconnect()
        >>> def disconnect():
        >>>     reason = app.current_event.request_context.disconnect_reason
        """
        return self.route(route_key=ROUTE_KEY_DISCONNECT, middlewares=middlewares)

    def on_default(
        self,
        middlewares: list[Callable] | None = None,
    ) -> Callable:
        """
        Register a handler for the `$default` route key.

        Invoked when the route selection expression does not match any custom route,
        or when the API has no custom routes.

        Parameters
        ----------
        middlewares : list[Callable], optional
            Middlewares to run around the handler for this route

        Returns
        -------
        Callable
            Decorator function that registers the default handler

        Examples
        --------
        >>> from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
        >>>
        >>> app = APIGatewayWebSocketResolver()
        >>>
        >>> @app.on_default()
        >>> def default():
        >>>     return {"echo": app.current_event.body}
        """
        return self.route(route_key=ROUTE_KEY_DEFAULT, middlewares=middlewares)

    def use(self, middlewares: list[Callable]) -> None:
        """
        Add one or more global middlewares that run before route-specific middlewares.

        Middlewares run in insertion order: global middlewares first, then route-level
        `middlewares=[...]`, then the route handler.

        Parameters
        ----------
        middlewares : list[Callable]
            List of middlewares to run on every event, including unmatched route keys

        Examples
        --------
        >>> from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
        >>> from aws_lambda_powertools.event_handler.middlewares import NextMiddleware
        >>>
        >>> app = APIGatewayWebSocketResolver()
        >>>
        >>> def log_route(app: APIGatewayWebSocketResolver, next_middleware: NextMiddleware):
        >>>     print(f"dispatching {app.current_event.request_context.route_key}")
        >>>     return next_middleware(app)
        >>>
        >>> app.use(middlewares=[log_route])
        """
        self._router_middlewares.extend(middlewares)

    def exception_handler(self, exc_class: type[Exception] | list[type[Exception]]) -> Callable:
        """
        Register a handler for one or more exception types.

        The handler receives the exception and its return value goes through the
        same response normalization as route handler return values.

        Parameters
        ----------
        exc_class : type[Exception] | list[type[Exception]]
            A single exception type or a list of exception types

        Returns
        -------
        Callable
            Decorator function that registers the exception handler

        Examples
        --------
        >>> from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
        >>>
        >>> app = APIGatewayWebSocketResolver()
        >>>
        >>> @app.exception_handler(ValueError)
        >>> def handle_invalid_value(exc: ValueError):
        >>>     return {"error": str(exc)}, 400
        """

        def register_exception_handler(func: Callable) -> Callable:
            if isinstance(exc_class, list):
                for exp in exc_class:
                    self._exception_handlers[exp] = func
            else:
                self._exception_handlers[exc_class] = func
            return func

        return register_exception_handler

    def append_context(self, **additional_context) -> None:
        """Append key=value data as routing context"""
        self.context.update(**additional_context)

    def clear_context(self) -> None:
        """Resets routing context"""
        self.context.clear()
