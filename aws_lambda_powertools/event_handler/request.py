"""Resolved HTTP Request object for Event Handler."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent


class Request:
    """Represents the resolved HTTP request.

    Provides structured access to the matched route pattern, extracted path parameters,
    HTTP method, headers, query parameters, body, the full Powertools proxy event
    (``resolved_event``), and the shared resolver context (``context``).

    Available via ``app.request`` inside middleware and, when added as a type-annotated
    parameter, inside ``Depends()`` dependency functions and route handlers.

    Examples
    --------
    **Dependency injection with Depends()**

    ```python
    from typing import Annotated
    from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Request, Depends

    app = APIGatewayRestResolver()

    def get_auth_user(request: Request) -> str:
        # Full event access via resolved_event
        token = request.resolved_event.get_header_value("authorization", default_value="")
        user = validate_token(token)
        # Bridge with middleware via shared context
        request.context["user"] = user
        return user

    @app.get("/orders")
    def list_orders(user: Annotated[str, Depends(get_auth_user)]):
        return {"user": user}
    ```

    **Middleware usage**

    ```python
    from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Request, Response
    from aws_lambda_powertools.event_handler.middlewares import NextMiddleware

    app = APIGatewayRestResolver()

    def auth_middleware(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
        request: Request = app.request

        route = request.route              # "/applications/{application_id}"
        path_params = request.path_parameters  # {"application_id": "4da715ee-..."}
        method = request.method            # "PUT"

        if not is_authorized(route, method, path_params):
            return Response(status_code=403, body="Forbidden")

        return next_middleware(app)

    app.use(middlewares=[auth_middleware])
    ```
    """

    __slots__ = ("_context", "_current_event", "_path_parameters", "_route_path")

    def __init__(
        self,
        route_path: str,
        path_parameters: dict[str, Any],
        current_event: BaseProxyEvent,
        context: dict[str, Any] | None = None,
    ) -> None:
        self._route_path = route_path
        self._path_parameters = path_parameters
        self._current_event = current_event
        self._context = context if context is not None else {}

    @property
    def route(self) -> str:
        """Matched route pattern in OpenAPI path-template format.

        Examples
        --------
        For a route registered as ``/applications/<application_id>`` the value is
        ``/applications/{application_id}``.
        """
        return self._route_path

    @property
    def path_parameters(self) -> dict[str, Any]:
        """Extracted path parameters for the matched route.

        Examples
        --------
        For a request to ``/applications/4da715ee``, matched against
        ``/applications/<application_id>``, the value is
        ``{"application_id": "4da715ee"}``.
        """
        return self._path_parameters

    @property
    def method(self) -> str:
        """HTTP method in upper-case, e.g. ``"GET"``, ``"PUT"``."""
        return self._current_event.http_method.upper()

    @property
    def headers(self) -> dict[str, str]:
        """Request headers dict (lower-cased keys may vary by event source)."""
        return self._current_event.headers or {}

    @property
    def query_parameters(self) -> dict[str, str] | None:
        """Query string parameters, or ``None`` when none are present."""
        return self._current_event.query_string_parameters

    @property
    def body(self) -> str | None:
        """Raw request body string, or ``None`` when the request has no body."""
        return self._current_event.body

    @property
    def json_body(self) -> Any:
        """Request body deserialized as a Python object (dict / list), or ``None``."""
        return self._current_event.json_body

    @property
    def resolved_event(self) -> BaseProxyEvent:
        """Full Powertools proxy event with all helpers and properties.

        Provides access to the complete ``BaseProxyEvent`` (or subclass) that
        Powertools resolved for the current invocation. This includes cookies,
        request context, path, and event-source-specific properties that are not
        available through the convenience properties on :class:`Request`.

        Examples
        --------
        ```python
        def get_request_details(request: Request) -> dict:
            event = request.resolved_event
            return {
                "path": event.path,
                "cookies": event.cookies,
                "request_context": event.request_context,
            }
        ```
        """
        return self._current_event

    @property
    def context(self) -> dict[str, Any]:
        """Shared resolver context (``app.context``) for this invocation.

        Provides read/write access to the same ``dict`` that middleware and
        ``app.append_context()`` populate. This enables incremental migration
        from middleware-based data sharing to ``Depends()``-based injection:
        middleware writes to ``app.context``, dependencies read from
        ``request.context``.

        Examples
        --------
        ```python
        def get_current_user(request: Request) -> dict:
            return request.context["user"]
        ```
        """
        return self._context
