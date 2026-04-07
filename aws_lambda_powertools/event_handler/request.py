"""Resolved HTTP Request object for Event Handler."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent


class Request:
    """Represents the resolved HTTP request.

    Provides structured access to the matched route pattern, extracted path parameters,
    HTTP method, headers, query parameters, and body.  Available via ``app.request``
    inside middleware and, when added as a type-annotated parameter, inside route handlers.

    Examples
    --------
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

    **Route handler injection (type-annotated)**

    ```python
    from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Request

    app = APIGatewayRestResolver()

    @app.get("/applications/<application_id>")
    def get_application(application_id: str, request: Request):
        user_agent = request.headers.get("user-agent")
        return {"id": application_id, "user_agent": user_agent}
    ```
    """

    __slots__ = ("_current_event", "_path_parameters", "_route_path")

    def __init__(
        self,
        route_path: str,
        path_parameters: dict[str, Any],
        current_event: BaseProxyEvent,
    ) -> None:
        self._route_path = route_path
        self._path_parameters = path_parameters
        self._current_event = current_event

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
