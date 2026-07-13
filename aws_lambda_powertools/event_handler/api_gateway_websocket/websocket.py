from __future__ import annotations

import json
import logging
import warnings
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.event_handler.api_gateway import MiddlewareFrame
from aws_lambda_powertools.event_handler.api_gateway_websocket.router import Router
from aws_lambda_powertools.event_handler.api_gateway_websocket.types import WebSocketRoute
from aws_lambda_powertools.event_handler.exception_handling import ExceptionHandlerManager
from aws_lambda_powertools.shared.json_encoder import Encoder
from aws_lambda_powertools.utilities.data_classes.api_gateway_websocket_event import APIGatewayWebSocketEvent
from aws_lambda_powertools.warnings import PowertoolsUserWarning

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.typing.lambda_context import LambdaContext

logger = logging.getLogger(__name__)


def _registered_route_adapter(app: APIGatewayWebSocketResolver, next_middleware: Callable[..., Any]) -> Any:
    """Terminal middleware frame: calls the registered route handler (no arguments) and returns its raw value.

    Response normalization happens once, after the whole middleware chain returns, so middlewares
    may short-circuit with any of the same shapes route handlers can return.
    """
    return next_middleware()


def _route_not_found() -> tuple[None, int]:
    """Stand-in handler for unmatched route keys, so global middlewares still run around the 400."""
    return None, HTTPStatus.BAD_REQUEST.value


class APIGatewayWebSocketResolver(Router):
    """
    API Gateway WebSocket API resolver.

    Dispatches WebSocket events to handlers registered by route key (`$connect`,
    `$disconnect`, `$default`, or custom route keys selected by the API's route
    selection expression) and normalizes handler return values into the
    `{"statusCode": ..., "body": ...}` shape API Gateway expects.

    Handlers take no arguments and access the request through `app.current_event`
    (an `APIGatewayWebSocketEvent`), `app.lambda_context`, and `app.context`.

    Attributes
    ----------
    context: dict
        Dictionary to store context information accessible across route handlers
    current_event: APIGatewayWebSocketEvent
        Current event being processed
    lambda_context: LambdaContext
        Lambda context from the AWS Lambda function

    Examples
    --------
    >>> from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
    >>>
    >>> app = APIGatewayWebSocketResolver()
    >>>
    >>> @app.on_connect()
    >>> def connect():
    >>>     return None  # 200: accept the connection
    >>>
    >>> @app.on_disconnect()
    >>> def disconnect():
    >>>     connection_id = app.current_event.request_context.connection_id
    >>>
    >>> @app.route("orderUpdate")
    >>> def order_update():
    >>>     return {"orderId": app.current_event.json_body["id"]}
    >>>
    >>> @app.on_default()
    >>> def default():
    >>>     return {"echo": app.current_event.body}
    >>>
    >>> def lambda_handler(event, context):
    >>>     return app.resolve(event, context)
    """

    def __init__(self):
        super().__init__()
        self.exception_handler_manager = ExceptionHandlerManager()
        self.processed_stack_frames: list[str] = []  # used by MiddlewareFrame for debug traces

    def __call__(
        self,
        event: dict | APIGatewayWebSocketEvent,
        context: LambdaContext,
    ) -> dict[str, Any]:
        """Implicit lambda handler which internally calls `resolve`."""
        return self.resolve(event, context)

    def resolve(
        self,
        event: dict | APIGatewayWebSocketEvent,
        context: LambdaContext,
    ) -> dict[str, Any]:
        """
        Resolve a WebSocket event to the handler registered for its route key.

        Parameters
        ----------
        event: dict | APIGatewayWebSocketEvent
            The API Gateway WebSocket event to process
        context: LambdaContext
            The Lambda context

        Returns
        -------
        dict[str, Any]
            The normalized Lambda response, always containing `statusCode` and
            optionally `body`. On `$connect`, a non-2xx status code rejects the
            connection; on other routes the body is delivered back to the client
            only when the route has a route response configured.

        Examples
        --------
        >>> app = APIGatewayWebSocketResolver()
        >>>
        >>> def lambda_handler(event, context):
        >>>     return app.resolve(event, context)
        """
        try:
            self.processed_stack_frames.clear()
            self._setup_context(event, context)
            return self._resolve_route()
        except Exception as exc:
            return self._handle_exception(exc)
        finally:
            self.clear_context()

    def exception_handler(self, exc_class: type[Exception] | list[type[Exception]]) -> Callable:
        """
        Register a handler for one or more exception types.

        The handler receives the exception and its return value goes through the
        same response normalization as route handler return values. Exceptions
        with no registered handler are logged and become a bare
        `{"statusCode": 500}` so no exception details reach the client.

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
        return self.exception_handler_manager.exception_handler(exc_class=exc_class)

    def include_router(self, router: Router) -> None:
        """
        Add all routes, middlewares, exception handlers, and context defined in a router.

        Parameters
        ----------
        router : Router
            A router containing routes to include, typically defined in a separate module

        Examples
        --------
        >>> # orders.py
        >>> from aws_lambda_powertools.event_handler.api_gateway_websocket import Router
        >>>
        >>> router = Router()
        >>>
        >>> @router.route("orderUpdate")
        >>> def order_update():
        >>>     return {"orderId": router.current_event.json_body["orderId"]}
        >>>
        >>> # app.py
        >>> import orders
        >>> from aws_lambda_powertools.event_handler import APIGatewayWebSocketResolver
        >>>
        >>> app = APIGatewayWebSocketResolver()
        >>> app.include_router(orders.router)
        """
        logger.debug("Merging router and app context")
        self.context.update(**router.context)
        # use pointer to allow context clearance after event is processed e.g., resolve(evt, ctx)
        router.context = self.context

        logger.debug("Merging router routes, middlewares, and exception handlers")
        self._router_middlewares.extend(router._router_middlewares)
        self._route_registry.merge(router._route_registry)
        self.exception_handler_manager.update_exception_handlers(router._exception_handlers)

    def _resolve_route(self) -> dict[str, Any]:
        """Dispatch the current event through the middleware chain to its route handler and normalize the response."""
        route_key = self.current_event.request_context.route_key
        route = self._route_registry.find_route(route_key)
        if route is None:
            warnings.warn(
                f"No route handler registered for route key `{route_key}`.",
                stacklevel=2,
                category=PowertoolsUserWarning,
            )
            # global middlewares still run around the 400, as REST does for not-found routes
            route = WebSocketRoute(func=_route_not_found, middlewares=[])

        logger.debug(f"Dispatching route key `{route_key}` to `{route['func'].__name__}`")
        middleware_stack = self._build_middleware_stack(route)
        return self._to_response(middleware_stack(self))

    def _build_middleware_stack(self, route: WebSocketRoute) -> Callable:
        """Wrap the route handler in middleware frames: global (`use`) first, then route-level, then
        the terminal adapter that calls the handler. Frames are wrapped in reverse so middlewares
        run in the order they were added."""
        stack: Callable = route["func"]
        all_middlewares = [*self._router_middlewares, *route["middlewares"], _registered_route_adapter]
        for middleware in reversed(all_middlewares):
            stack = MiddlewareFrame(current_middleware=middleware, next_middleware=stack)
        return stack

    def _push_processed_stack_frame(self, frame: str) -> None:
        """Record a processed middleware frame; MiddlewareFrame calls this for debug traces."""
        self.processed_stack_frames.append(frame)

    def _handle_exception(self, exc: Exception) -> dict[str, Any]:
        """Resolve an exception to a response via registered handlers, or a bare 500.

        An unhandled exception must never propagate to the Lambda runtime: the runtime's
        default error response (exception type, message, and stack trace) is delivered
        to the connected client.
        """
        handler = self.exception_handler_manager.lookup_exception_handler(type(exc))
        if handler:
            try:
                return self._to_response(handler(exc))
            except Exception:
                logger.exception("Exception handler raised an exception")
                return {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value}

        logger.exception(f"Unhandled exception while resolving route key `{self._safe_route_key()}`")
        return {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value}

    def _safe_route_key(self) -> str:
        """Best-effort route key for logging, tolerating malformed events."""
        try:
            return self.current_event.request_context.route_key
        except Exception:
            return "<unknown>"

    def _to_response(self, result: Any) -> dict[str, Any]:
        """Normalize a handler return value into the Lambda response shape.

        A 2-tuple sets the status code explicitly; any other value maps to 200.
        A returned dict is always body content — it is never inspected for a
        `statusCode` key.
        """
        if isinstance(result, tuple) and len(result) == 2:
            body, status_code = result
            return self._format_response(body, int(status_code))
        return self._format_response(result, HTTPStatus.OK.value)

    def _format_response(self, body: Any, status_code: int) -> dict[str, Any]:
        if body is None:
            return {"statusCode": status_code}
        if isinstance(body, str):
            return {"statusCode": status_code, "body": body}
        return {"statusCode": status_code, "body": json.dumps(body, separators=(",", ":"), cls=Encoder)}

    def _setup_context(self, event: dict | APIGatewayWebSocketEvent, context: LambdaContext) -> None:
        """Set up the current event and context, shared with included routers via class attributes."""
        self.lambda_context = context
        Router.lambda_context = context

        Router.current_event = event if isinstance(event, APIGatewayWebSocketEvent) else APIGatewayWebSocketEvent(event)
        self.current_event = Router.current_event
