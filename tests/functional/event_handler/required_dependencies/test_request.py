"""Tests for the Request object feature (GH #7992).

Covers:
- ``app.request`` availability in global and route-level middleware
- ``Request`` type-annotation injection in route handlers
- ``Request`` properties: route, path_parameters, method, headers, query_parameters, body
- ``RuntimeError`` when ``app.request`` is accessed outside of resolution
- Backward compatibility: routes without ``Request`` continue to work unchanged
- ``APIGatewayHttpResolver`` and ``ALBResolver`` variants
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aws_lambda_powertools.event_handler import (
    ALBResolver,
    APIGatewayHttpResolver,
    APIGatewayRestResolver,
    Request,
    Response,
)
from tests.functional.utils import load_event

if TYPE_CHECKING:
    from aws_lambda_powertools.event_handler.middlewares import NextMiddleware

# ---------------------------------------------------------------------------
# Shared test events
# ---------------------------------------------------------------------------

API_REST_EVENT = load_event("apiGatewayProxyEvent.json")  # GET /my/path
API_RESTV2_EVENT = load_event("apiGatewayProxyV2Event_GET.json")


def _make_rest_event(path: str, method: str = "GET", path_parameters: dict | None = None, body: str | None = None):
    """Build a minimal API Gateway REST (v1) proxy event."""
    return {
        "httpMethod": method,
        "path": path,
        "pathParameters": path_parameters,
        "queryStringParameters": None,
        "multiValueQueryStringParameters": None,
        "headers": {"Content-Type": "application/json", "user-agent": "pytest"},
        "multiValueHeaders": {},
        "body": body,
        "isBase64Encoded": False,
        "requestContext": {"httpMethod": method, "resourcePath": path},
        "resource": path,
        "stageVariables": None,
    }


# ---------------------------------------------------------------------------
# app.request in global middleware
# ---------------------------------------------------------------------------


def test_request_available_in_global_middleware():
    app = APIGatewayRestResolver()
    captured: list[Request] = []

    def capture_middleware(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
        captured.append(app.request)
        return next_middleware(app)

    app.use(middlewares=[capture_middleware])

    @app.get("/my/path")
    def handler():
        return {}

    app(API_REST_EVENT, {})

    assert len(captured) == 1
    req = captured[0]
    assert isinstance(req, Request)
    assert req.route == "/my/path"
    assert req.method == "GET"


def test_request_route_pattern_uses_openapi_format():
    """route property should use {param} OpenAPI notation, not <param> Powertools notation."""
    app = APIGatewayRestResolver()
    captured: list[Request] = []

    def mw(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
        captured.append(app.request)
        return next_middleware(app)

    app.use(middlewares=[mw])

    @app.get("/applications/<application_id>")
    def handler(application_id: str):
        return {}

    event = _make_rest_event(
        "/applications/42",
        path_parameters={"application_id": "42"},
    )
    app(event, {})

    assert captured[0].route == "/applications/{application_id}"


def test_request_path_parameters_in_middleware():
    app = APIGatewayRestResolver()
    captured: list[dict] = []

    def mw(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
        captured.append(app.request.path_parameters)
        return next_middleware(app)

    app.use(middlewares=[mw])

    @app.get("/applications/<application_id>")
    def handler(application_id: str):
        return {}

    event = _make_rest_event(
        "/applications/4da715ee",
        path_parameters={"application_id": "4da715ee"},
    )
    app(event, {})

    assert captured == [{"application_id": "4da715ee"}]


def test_request_method_in_middleware():
    app = APIGatewayRestResolver()
    methods_seen: list[str] = []

    def mw(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
        methods_seen.append(app.request.method)
        return next_middleware(app)

    app.use(middlewares=[mw])

    @app.put("/items/<item_id>")
    def handler(item_id: str):
        return {}

    event = _make_rest_event("/items/99", method="PUT", path_parameters={"item_id": "99"})
    app(event, {})

    assert methods_seen == ["PUT"]


def test_request_headers_in_middleware():
    app = APIGatewayRestResolver()
    headers_seen: list[dict] = []

    def mw(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
        headers_seen.append(app.request.headers)
        return next_middleware(app)

    app.use(middlewares=[mw])

    @app.get("/my/path")
    def handler():
        return {}

    app(API_REST_EVENT, {})

    assert len(headers_seen) == 1
    # headers is a dict (may have varying casing depending on event source)
    assert isinstance(headers_seen[0], dict)


def test_request_query_parameters_in_middleware():
    app = APIGatewayRestResolver()
    captured: list = []

    def mw(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
        captured.append(app.request.query_parameters)
        return next_middleware(app)

    app.use(middlewares=[mw])

    @app.get("/search")
    def handler():
        return {}

    event = _make_rest_event("/search")
    event["queryStringParameters"] = {"q": "powertools"}
    app(event, {})

    assert captured == [{"q": "powertools"}]


def test_request_body_in_middleware():
    app = APIGatewayRestResolver()
    bodies_seen: list = []

    def mw(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
        bodies_seen.append(app.request.body)
        return next_middleware(app)

    app.use(middlewares=[mw])

    @app.post("/items")
    def handler():
        return {}

    event = _make_rest_event("/items", method="POST", body='{"name": "widget"}')
    event["httpMethod"] = "POST"
    app(event, {})

    assert bodies_seen == ['{"name": "widget"}']


# ---------------------------------------------------------------------------
# Request injection in route handlers via type annotation
# ---------------------------------------------------------------------------


def test_request_injected_into_handler():
    app = APIGatewayRestResolver()

    received: list[Request] = []

    @app.get("/my/path")
    def handler(request: Request):
        received.append(request)
        return {}

    app(API_REST_EVENT, {})

    assert len(received) == 1
    assert isinstance(received[0], Request)
    assert received[0].route == "/my/path"
    assert received[0].method == "GET"


def test_request_injected_alongside_path_params():
    app = APIGatewayRestResolver()

    received: list[tuple] = []

    @app.get("/users/<user_id>")
    def handler(user_id: str, request: Request):
        received.append((user_id, request))
        return {}

    event = _make_rest_event("/users/123", path_parameters={"user_id": "123"})
    app(event, {})

    assert len(received) == 1
    user_id, req = received[0]
    assert user_id == "123"
    assert isinstance(req, Request)
    assert req.path_parameters == {"user_id": "123"}
    assert req.route == "/users/{user_id}"


def test_request_injection_parameter_name_is_flexible():
    """The parameter can be named anything as long as it is annotated as Request."""
    app = APIGatewayRestResolver()

    received: list[Request] = []

    @app.get("/my/path")
    def handler(req: Request):
        received.append(req)
        return {}

    app(API_REST_EVENT, {})

    assert received[0].route == "/my/path"


def test_handler_without_request_annotation_unaffected():
    """Existing handlers with no Request annotation continue to work identically."""
    app = APIGatewayRestResolver()

    @app.get("/my/path")
    def handler():
        return {"ok": True}

    result = app(API_REST_EVENT, {})
    assert result["statusCode"] == 200


def test_handler_with_path_params_only_unaffected():
    """Handlers that only use path params continue to work identically."""
    app = APIGatewayRestResolver()

    @app.get("/users/<user_id>")
    def handler(user_id: str):
        return {"id": user_id}

    event = _make_rest_event("/users/42", path_parameters={"user_id": "42"})
    result = app(event, {})
    assert result["statusCode"] == 200


# ---------------------------------------------------------------------------
# Request injection caching (idempotency across multiple calls)
# ---------------------------------------------------------------------------


def test_request_injection_works_across_multiple_invocations():
    """Injection must work correctly on repeated calls (cached param name must stay valid)."""
    app = APIGatewayRestResolver()
    call_count = 0

    @app.get("/counters/<counter_id>")
    def handler(counter_id: str, request: Request):
        nonlocal call_count
        call_count += 1
        assert request.path_parameters["counter_id"] == counter_id
        return {}

    for i in range(3):
        event = _make_rest_event(f"/counters/{i}", path_parameters={"counter_id": str(i)})
        result = app(event, {})
        assert result["statusCode"] == 200

    assert call_count == 3


# ---------------------------------------------------------------------------
# RuntimeError when accessed outside of request resolution
# ---------------------------------------------------------------------------


def test_request_raises_before_resolution():
    app = APIGatewayRestResolver()
    with pytest.raises(RuntimeError, match="app.request is only available after route resolution"):
        _ = app.request


# ---------------------------------------------------------------------------
# Route-level middleware also gets app.request
# ---------------------------------------------------------------------------


def test_request_available_in_route_level_middleware():
    app = APIGatewayRestResolver()
    captured: list[Request] = []

    def route_mw(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
        captured.append(app.request)
        return next_middleware(app)

    @app.get("/protected/<resource_id>", middlewares=[route_mw])
    def handler(resource_id: str):
        return {}

    event = _make_rest_event("/protected/abc", path_parameters={"resource_id": "abc"})
    app(event, {})

    assert len(captured) == 1
    assert captured[0].route == "/protected/{resource_id}"
    assert captured[0].path_parameters == {"resource_id": "abc"}


# ---------------------------------------------------------------------------
# Other resolver types
# ---------------------------------------------------------------------------


def test_request_available_in_http_resolver_middleware():
    app = APIGatewayHttpResolver()
    captured: list[Request] = []

    def mw(app, next_middleware):
        captured.append(app.request)
        return next_middleware(app)

    app.use(middlewares=[mw])

    @app.get("/my/path")
    def handler():
        return {}

    app(API_RESTV2_EVENT, {})

    assert len(captured) == 1
    assert captured[0].method == "GET"


def test_request_available_in_alb_middleware():
    alb_event = load_event("albEvent.json")
    app = ALBResolver()
    captured: list[Request] = []

    def mw(app, next_middleware):
        captured.append(app.request)
        return next_middleware(app)

    app.use(middlewares=[mw])

    # Register a route that matches the ALB event's path
    path = alb_event.get("path", "/lambda")

    @app.get(path)
    def handler():
        return {}

    app(alb_event, {})

    assert len(captured) == 1
    assert isinstance(captured[0], Request)


# ---------------------------------------------------------------------------
# Router / include_router pattern
# ---------------------------------------------------------------------------


def test_request_available_in_middleware_with_include_router():
    """app.request must work in middleware when routes come from an included Router."""
    from aws_lambda_powertools.event_handler.api_gateway import Router

    app = APIGatewayRestResolver()
    router = Router()
    captured: list[Request] = []

    def mw(app, next_middleware):
        captured.append(app.request)
        return next_middleware(app)

    app.use(middlewares=[mw])

    @router.get("/users/<user_id>")
    def get_user(user_id: str):
        return {"id": user_id}

    app.include_router(router)

    event = _make_rest_event("/users/abc", path_parameters={"user_id": "abc"})
    result = app(event, {})

    assert result["statusCode"] == 200
    assert len(captured) == 1
    assert captured[0].route == "/users/{user_id}"
    assert captured[0].path_parameters == {"user_id": "abc"}


def test_request_injected_in_handler_with_include_router():
    """Request injection via type annotation must work when routes come from an included Router."""
    from aws_lambda_powertools.event_handler.api_gateway import Router

    app = APIGatewayRestResolver()
    router = Router()
    received: list[Request] = []

    @router.get("/items/<item_id>")
    def get_item(item_id: str, request: Request):
        received.append(request)
        return {"id": item_id}

    app.include_router(router)

    event = _make_rest_event("/items/xyz", path_parameters={"item_id": "xyz"})
    result = app(event, {})

    assert result["statusCode"] == 200
    assert len(received) == 1
    assert received[0].route == "/items/{item_id}"
    assert received[0].path_parameters == {"item_id": "xyz"}


# ---------------------------------------------------------------------------
# Proxy+ use case (the original issue scenario)
# ---------------------------------------------------------------------------


def test_request_resolves_path_params_from_proxy_plus_event():
    """When API GW uses {proxy+}, app.current_event.pathParameters only has 'proxy'.
    But app.request.path_parameters should have the *resolved* params from Powertools routing."""
    app = APIGatewayRestResolver()
    captured: list[Request] = []

    def auth_middleware(app, next_middleware):
        captured.append(app.request)
        return next_middleware(app)

    app.use(middlewares=[auth_middleware])

    @app.get("/applications/<application_id>")
    def get_application(application_id: str):
        return {"id": application_id}

    @app.put("/applications/<application_id>")
    def put_application(application_id: str):
        return {"updated": application_id}

    # Simulate a proxy+ event where API GW only knows about {proxy+}
    event = {
        "httpMethod": "PUT",
        "path": "/applications/4da715ee-79d4-4e52-81cb-1ecc464708fb",
        "pathParameters": {"proxy": "4da715ee-79d4-4e52-81cb-1ecc464708fb"},
        "queryStringParameters": None,
        "multiValueQueryStringParameters": None,
        "headers": {"Content-Type": "application/json"},
        "multiValueHeaders": {},
        "body": None,
        "isBase64Encoded": False,
        "requestContext": {"httpMethod": "PUT", "resourcePath": "/applications/{proxy+}"},
        "resource": "/applications/{proxy+}",
        "stageVariables": None,
    }

    result = app(event, {})

    assert result["statusCode"] == 200
    assert len(captured) == 1

    req = captured[0]
    # Middleware sees the resolved route, NOT the proxy+ pattern
    assert req.route == "/applications/{application_id}"
    assert req.path_parameters == {"application_id": "4da715ee-79d4-4e52-81cb-1ecc464708fb"}
    assert req.method == "PUT"


# ---------------------------------------------------------------------------
# Missing coverage: json_body, query_parameters=None, request caching
# ---------------------------------------------------------------------------


def test_request_json_body_in_middleware():
    app = APIGatewayRestResolver()
    bodies_seen: list = []

    def mw(app: APIGatewayRestResolver, next_middleware):
        bodies_seen.append(app.request.json_body)
        return next_middleware(app)

    app.use(middlewares=[mw])

    @app.post("/items")
    def handler():
        return {}

    event = _make_rest_event("/items", method="POST", body='{"name": "widget"}')
    app(event, {})

    assert bodies_seen == [{"name": "widget"}]


def test_request_query_parameters_empty():
    """When no query string parameters are present, query_parameters returns empty or None."""
    app = APIGatewayRestResolver()
    captured: list = []

    def mw(app: APIGatewayRestResolver, next_middleware):
        captured.append(app.request.query_parameters)
        return next_middleware(app)

    app.use(middlewares=[mw])

    @app.get("/my/path")
    def handler():
        return {}

    event = _make_rest_event("/my/path")
    app(event, {})

    # No query params present — should be falsy (empty dict or None depending on event source)
    assert not captured[0]


def test_request_is_cached_across_multiple_accesses():
    """Accessing app.request multiple times in the same invocation returns the same object."""
    app = APIGatewayRestResolver()
    ids_seen: list[int] = []

    def mw(app: APIGatewayRestResolver, next_middleware):
        ids_seen.append(id(app.request))
        ids_seen.append(id(app.request))
        return next_middleware(app)

    app.use(middlewares=[mw])

    @app.get("/my/path")
    def handler(request: Request):
        ids_seen.append(id(request))
        return {}

    app(API_REST_EVENT, {})

    # All accesses should return the same cached instance
    assert len(ids_seen) == 3
    assert ids_seen[0] == ids_seen[1] == ids_seen[2]


# ---------------------------------------------------------------------------
# resolved_event — full Powertools proxy event access
# ---------------------------------------------------------------------------


def test_request_resolved_event_exposes_full_event():
    """resolved_event should return the full BaseProxyEvent with all helpers."""
    app = APIGatewayRestResolver()
    captured: list[Request] = []

    def mw(app: APIGatewayRestResolver, next_middleware):
        captured.append(app.request)
        return next_middleware(app)

    app.use(middlewares=[mw])

    @app.get("/my/path")
    def handler():
        return {}

    app(API_REST_EVENT, {})

    req = captured[0]
    resolved = req.resolved_event

    # resolved_event should be the same object as app.current_event
    assert resolved is not None
    assert resolved.http_method == "GET"
    # Should have helper methods not available on Request directly
    assert hasattr(resolved, "get_header_value")
    assert hasattr(resolved, "get_query_string_value")


def test_request_resolved_event_provides_cookies_and_path():
    """resolved_event gives access to path and properties not on Request."""
    app = APIGatewayRestResolver()
    captured: list[Request] = []

    def mw(app: APIGatewayRestResolver, next_middleware):
        captured.append(app.request)
        return next_middleware(app)

    app.use(middlewares=[mw])

    @app.get("/items/<item_id>")
    def handler(item_id: str):
        return {}

    event = _make_rest_event("/items/42", path_parameters={"item_id": "42"})
    app(event, {})

    resolved = captured[0].resolved_event
    assert resolved.path == "/items/42"


# ---------------------------------------------------------------------------
# context — shared resolver context (app.context)
# ---------------------------------------------------------------------------


def test_request_context_shares_app_context():
    """request.context should be the same dict as app.context."""
    app = APIGatewayRestResolver()

    def mw(app: APIGatewayRestResolver, next_middleware):
        app.append_context(user="test-user")
        return next_middleware(app)

    app.use(middlewares=[mw])

    @app.get("/my/path")
    def handler(request: Request):
        return {"user": request.context.get("user")}

    result = app(API_REST_EVENT, {})
    assert result["statusCode"] == 200
    import json

    assert json.loads(result["body"]) == {"user": "test-user"}
