"""Tests for HttpResolverAlpha - ASGI-compatible HTTP resolver for local development."""

from __future__ import annotations

import asyncio
import json
from typing import Annotated

import pytest
from pydantic import BaseModel, Field

from aws_lambda_powertools.event_handler import HttpResolverAlpha, Response
from aws_lambda_powertools.event_handler.http_resolver import (
    HttpProxyEvent,
    MockLambdaContext,
)
from aws_lambda_powertools.event_handler.openapi.params import Query

# Suppress alpha warning for all tests
pytestmark = pytest.mark.filterwarnings("ignore:HttpResolverAlpha is an alpha feature")


# =============================================================================
# Test Models
# =============================================================================


class UserModel(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    email: str | None = None


class UserResponse(BaseModel):
    id: str
    user: UserModel
    created: bool = True


# =============================================================================
# HttpProxyEvent Tests
# =============================================================================


def test_http_proxy_event_basic():
    """Test creating a basic HTTP event."""
    event = HttpProxyEvent(
        method="GET",
        path="/users/123",
        headers={"content-type": "application/json"},
    )

    assert event.http_method == "GET"
    assert event.path == "/users/123"
    assert event.headers.get("content-type") == "application/json"


def test_http_proxy_event_with_body():
    """Test creating an event with a JSON body."""
    body = '{"name": "test"}'
    event = HttpProxyEvent(
        method="POST",
        path="/users",
        headers={"content-type": "application/json"},
        body=body,
    )

    assert event.body == body
    assert event.json_body == {"name": "test"}


def test_http_proxy_event_with_bytes_body():
    """Test creating an event with bytes body."""
    body = b'{"name": "test"}'
    event = HttpProxyEvent(
        method="POST",
        path="/users",
        body=body,
    )

    assert event.body == '{"name": "test"}'


def test_http_proxy_event_query_string_parsing():
    """Test query string is parsed correctly."""
    event = HttpProxyEvent(
        method="GET",
        path="/search",
        query_string="q=python&page=1&tags=aws&tags=lambda",
    )

    assert event.query_string_parameters.get("q") == "python"
    assert event.query_string_parameters.get("page") == "1"
    assert event.multi_value_query_string_parameters.get("tags") == ["aws", "lambda"]


def test_http_proxy_event_from_asgi_scope():
    """Test creating event from ASGI scope."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/users/123",
        "query_string": b"include=details",
        "headers": [
            (b"content-type", b"application/json"),
            (b"authorization", b"Bearer token123"),
        ],
    }

    event = HttpProxyEvent.from_asgi(scope, body=None)

    assert event.http_method == "GET"
    assert event.path == "/users/123"
    assert event.headers.get("content-type") == "application/json"
    assert event.headers.get("authorization") == "Bearer token123"
    assert event.query_string_parameters.get("include") == "details"


def test_http_proxy_event_from_asgi_with_body():
    """Test creating event from ASGI scope with body."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/users",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
    }
    body = b'{"name": "John", "age": 30}'

    event = HttpProxyEvent.from_asgi(scope, body=body)

    assert event.json_body == {"name": "John", "age": 30}


def test_http_proxy_event_resolved_query_string_parameters():
    """Test resolved_query_string_parameters returns multi-value format."""
    event = HttpProxyEvent(
        method="GET",
        path="/search",
        query_string="tags=aws&tags=lambda",
    )

    resolved = event.resolved_query_string_parameters
    assert resolved.get("tags") == ["aws", "lambda"]


def test_http_proxy_event_resolved_headers_field():
    """Test resolved_headers_field returns headers."""
    event = HttpProxyEvent(
        method="GET",
        path="/test",
        headers={"X-Custom-Header": "value"},
    )

    assert event.resolved_headers_field.get("x-custom-header") == "value"


# =============================================================================
# HttpResolver Basic Tests
# =============================================================================


def test_simple_get_route():
    """Test a simple GET route."""
    app = HttpResolverAlpha()

    @app.get("/hello")
    def hello():
        return {"message": "Hello, World!"}

    event = {
        "httpMethod": "GET",
        "path": "/hello",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["message"] == "Hello, World!"


def test_path_parameters():
    """Test route with path parameters."""
    app = HttpResolverAlpha()

    @app.get("/users/<user_id>")
    def get_user(user_id: str):
        return {"user_id": user_id}

    event = {
        "httpMethod": "GET",
        "path": "/users/123",
        "headers": {},
        "queryStringParameters": {},
        "pathParameters": {"user_id": "123"},
        "body": None,
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["user_id"] == "123"


def test_post_with_body():
    """Test POST route with JSON body."""
    app = HttpResolverAlpha()

    @app.post("/users")
    def create_user():
        body = app.current_event.json_body
        return {"created": True, "name": body["name"]}

    event = {
        "httpMethod": "POST",
        "path": "/users",
        "headers": {"content-type": "application/json"},
        "queryStringParameters": {},
        "body": '{"name": "John"}',
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["created"] is True
    assert body["name"] == "John"


def test_query_parameters():
    """Test accessing query parameters."""
    app = HttpResolverAlpha()

    @app.get("/search")
    def search():
        q = app.current_event.get_query_string_value("q", "")
        page = app.current_event.get_query_string_value("page", "1")
        return {"query": q, "page": page}

    event = {
        "httpMethod": "GET",
        "path": "/search",
        "headers": {},
        "queryStringParameters": {"q": "python", "page": "2"},
        "multiValueQueryStringParameters": {"q": ["python"], "page": ["2"]},
        "body": None,
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["query"] == "python"
    assert body["page"] == "2"


def test_custom_response():
    """Test returning a custom Response object."""
    app = HttpResolverAlpha()

    @app.get("/custom")
    def custom():
        return Response(
            status_code=201,
            content_type="application/json",
            body={"status": "created"},
            headers={"X-Custom-Header": "value"},
        )

    event = {
        "httpMethod": "GET",
        "path": "/custom",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 201
    assert result["headers"]["X-Custom-Header"] == "value"


def test_not_found():
    """Test 404 response for unknown route."""
    app = HttpResolverAlpha()

    @app.get("/exists")
    def exists():
        return {"exists": True}

    event = {
        "httpMethod": "GET",
        "path": "/does-not-exist",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 404


def test_custom_not_found_handler():
    """Test custom not_found handler is called."""
    app = HttpResolverAlpha()

    @app.not_found
    def custom_not_found(exc: Exception):
        return Response(
            status_code=404,
            content_type="application/json",
            body={"error": "Custom Not Found", "path": app.current_event.path},
        )

    @app.get("/exists")
    def exists():
        return {"exists": True}

    event = {
        "httpMethod": "GET",
        "path": "/unknown-route",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 404
    body = json.loads(result["body"])
    assert body["error"] == "Custom Not Found"
    assert body["path"] == "/unknown-route"


# =============================================================================
# HttpResolver Validation Tests
# =============================================================================


def test_valid_body_validation():
    """Test valid request body passes validation."""
    app = HttpResolverAlpha(enable_validation=True)

    @app.post("/users")
    def create_user(user: UserModel) -> UserResponse:
        return UserResponse(id="user-123", user=user)

    event = {
        "httpMethod": "POST",
        "path": "/users",
        "headers": {"content-type": "application/json"},
        "queryStringParameters": {},
        "multiValueQueryStringParameters": {},
        "body": '{"name": "John", "age": 30}',
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["id"] == "user-123"
    assert body["user"]["name"] == "John"


def test_invalid_body_validation():
    """Test invalid request body fails validation."""
    app = HttpResolverAlpha(enable_validation=True)

    @app.post("/users")
    def create_user(user: UserModel) -> UserResponse:
        return UserResponse(id="user-123", user=user)

    event = {
        "httpMethod": "POST",
        "path": "/users",
        "headers": {"content-type": "application/json"},
        "queryStringParameters": {},
        "multiValueQueryStringParameters": {},
        "body": '{"name": "", "age": 30}',  # Empty name - invalid
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 422
    body = json.loads(result["body"])
    assert "detail" in body


def test_missing_required_field():
    """Test missing required field fails validation."""
    app = HttpResolverAlpha(enable_validation=True)

    @app.post("/users")
    def create_user(user: UserModel) -> UserResponse:
        return UserResponse(id="user-123", user=user)

    event = {
        "httpMethod": "POST",
        "path": "/users",
        "headers": {"content-type": "application/json"},
        "queryStringParameters": {},
        "multiValueQueryStringParameters": {},
        "body": '{"age": 30}',  # Missing name
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 422


def test_query_param_validation():
    """Test query parameter validation."""
    app = HttpResolverAlpha(enable_validation=True)

    @app.get("/search")
    def search(
        q: Annotated[str, Query(description="Search query")],
        page: Annotated[int, Query(ge=1)] = 1,
        limit: Annotated[int, Query(ge=1, le=100)] = 10,
    ) -> dict:
        return {"query": q, "page": page, "limit": limit}

    event = {
        "httpMethod": "GET",
        "path": "/search",
        "headers": {},
        "queryStringParameters": {"q": "python", "page": "2", "limit": "50"},
        "multiValueQueryStringParameters": {"q": ["python"], "page": ["2"], "limit": ["50"]},
        "body": None,
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["query"] == "python"
    assert body["page"] == 2
    assert body["limit"] == 50


def test_invalid_query_param():
    """Test invalid query parameter fails validation."""
    app = HttpResolverAlpha(enable_validation=True)

    @app.get("/search")
    def search(
        q: Annotated[str, Query()],
        limit: Annotated[int, Query(ge=1, le=100)] = 10,
    ) -> dict:
        return {"query": q, "limit": limit}

    event = {
        "httpMethod": "GET",
        "path": "/search",
        "headers": {},
        "queryStringParameters": {"q": "test", "limit": "200"},  # limit > 100
        "multiValueQueryStringParameters": {"q": ["test"], "limit": ["200"]},
        "body": None,
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 422


# =============================================================================
# HttpResolver Middleware Tests
# =============================================================================


def test_middleware_execution():
    """Test middleware is executed."""
    app = HttpResolverAlpha()
    middleware_called = []

    def test_middleware(app, next_middleware):
        middleware_called.append("before")
        response = next_middleware(app)
        middleware_called.append("after")
        return response

    app.use([test_middleware])

    @app.get("/test")
    def test_route():
        middleware_called.append("handler")
        return {"ok": True}

    event = {
        "httpMethod": "GET",
        "path": "/test",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 200
    assert middleware_called == ["before", "handler", "after"]


def test_middleware_can_short_circuit():
    """Test middleware can return early without calling handler."""
    app = HttpResolverAlpha()

    def auth_middleware(app, next_middleware):
        auth_header = app.current_event.headers.get("authorization")
        if not auth_header:
            return Response(status_code=401, body={"error": "Unauthorized"})
        return next_middleware(app)

    app.use([auth_middleware])

    @app.get("/protected")
    def protected():
        return {"secret": "data"}

    # Without auth header
    event = {
        "httpMethod": "GET",
        "path": "/protected",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    result = app.resolve(event, MockLambdaContext())
    assert result["statusCode"] == 401

    # With auth header
    event["headers"] = {"authorization": "Bearer token"}
    result = app.resolve(event, MockLambdaContext())
    assert result["statusCode"] == 200


def test_multiple_middlewares():
    """Test multiple middlewares execute in order."""
    app = HttpResolverAlpha()
    order = []

    def middleware_1(app, next_middleware):
        order.append("m1_before")
        response = next_middleware(app)
        order.append("m1_after")
        return response

    def middleware_2(app, next_middleware):
        order.append("m2_before")
        response = next_middleware(app)
        order.append("m2_after")
        return response

    app.use([middleware_1, middleware_2])

    @app.get("/test")
    def test_route():
        order.append("handler")
        return {"ok": True}

    event = {
        "httpMethod": "GET",
        "path": "/test",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    app.resolve(event, MockLambdaContext())

    assert order == ["m1_before", "m2_before", "handler", "m2_after", "m1_after"]


def test_route_specific_middleware():
    """Test middleware applied to specific route only."""
    app = HttpResolverAlpha()
    route_middleware_called = []

    def route_middleware(app, next_middleware):
        route_middleware_called.append("route_middleware")
        return next_middleware(app)

    @app.get("/with-middleware", middlewares=[route_middleware])
    def with_middleware():
        return {"has_middleware": True}

    @app.get("/without-middleware")
    def without_middleware():
        return {"has_middleware": False}

    # Test route WITH middleware
    event_with = {
        "httpMethod": "GET",
        "path": "/with-middleware",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    result = app.resolve(event_with, MockLambdaContext())
    assert result["statusCode"] == 200
    assert route_middleware_called == ["route_middleware"]

    # Reset and test route WITHOUT middleware
    route_middleware_called.clear()

    event_without = {
        "httpMethod": "GET",
        "path": "/without-middleware",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    result = app.resolve(event_without, MockLambdaContext())
    assert result["statusCode"] == 200
    assert route_middleware_called == []  # Middleware should NOT be called


def test_route_middleware_with_global_middleware():
    """Test route-specific middleware combined with global middleware."""
    app = HttpResolverAlpha()
    order = []

    def global_middleware(app, next_middleware):
        order.append("global_before")
        response = next_middleware(app)
        order.append("global_after")
        return response

    def route_middleware(app, next_middleware):
        order.append("route_before")
        response = next_middleware(app)
        order.append("route_after")
        return response

    app.use([global_middleware])

    @app.get("/test", middlewares=[route_middleware])
    def test_route():
        order.append("handler")
        return {"ok": True}

    event = {
        "httpMethod": "GET",
        "path": "/test",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    app.resolve(event, MockLambdaContext())

    # Global middleware runs first, then route middleware
    assert order == ["global_before", "route_before", "handler", "route_after", "global_after"]


def test_route_middleware_can_modify_response():
    """Test route middleware can modify the response."""
    app = HttpResolverAlpha()

    def add_header_middleware(app, next_middleware):
        response = next_middleware(app)
        response.headers["X-Custom-Header"] = "added-by-middleware"
        return response

    @app.get("/test", middlewares=[add_header_middleware])
    def test_route():
        return {"ok": True}

    event = {
        "httpMethod": "GET",
        "path": "/test",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    result = app.resolve(event, MockLambdaContext())

    assert result["statusCode"] == 200
    assert result["headers"]["X-Custom-Header"] == "added-by-middleware"


# =============================================================================
# HttpResolver ASGI Tests
# =============================================================================


@pytest.mark.asyncio
async def test_asgi_get_request():
    """Test ASGI GET request."""
    app = HttpResolverAlpha()

    @app.get("/hello/<name>")
    def hello(name: str):
        return {"message": f"Hello, {name}!"}

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/hello/World",
        "query_string": b"",
        "headers": [],
    }

    response_body = b""
    status_code = None

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        nonlocal response_body, status_code
        if message["type"] == "http.response.start":
            status_code = message["status"]
        elif message["type"] == "http.response.body":
            response_body = message["body"]

    await app(scope, receive, send)

    assert status_code == 200
    body = json.loads(response_body)
    assert body["message"] == "Hello, World!"


@pytest.mark.asyncio
async def test_asgi_custom_not_found():
    """Test custom not_found handler in ASGI mode."""
    app = HttpResolverAlpha()

    @app.not_found
    def custom_not_found(exc: Exception):
        return Response(
            status_code=404,
            content_type="application/json",
            body={"error": "Custom 404", "path": app.current_event.path},
        )

    @app.get("/exists")
    def exists():
        return {"exists": True}

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/unknown-asgi-route",
        "query_string": b"",
        "headers": [],
    }

    response_body = b""
    status_code = None

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        nonlocal response_body, status_code
        if message["type"] == "http.response.start":
            status_code = message["status"]
        elif message["type"] == "http.response.body":
            response_body = message["body"]

    await app(scope, receive, send)

    assert status_code == 404
    body = json.loads(response_body)
    assert body["error"] == "Custom 404"
    assert body["path"] == "/unknown-asgi-route"


@pytest.mark.asyncio
async def test_asgi_post_request():
    """Test ASGI POST request with body."""
    app = HttpResolverAlpha()

    @app.post("/users")
    def create_user():
        body = app.current_event.json_body
        return {"created": True, "name": body["name"]}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/users",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
    }

    request_body = b'{"name": "John"}'
    response_body = b""
    status_code = None

    async def receive():
        return {"type": "http.request", "body": request_body, "more_body": False}

    async def send(message):
        nonlocal response_body, status_code
        if message["type"] == "http.response.start":
            status_code = message["status"]
        elif message["type"] == "http.response.body":
            response_body = message["body"]

    await app(scope, receive, send)

    assert status_code == 200
    body = json.loads(response_body)
    assert body["created"] is True
    assert body["name"] == "John"


@pytest.mark.asyncio
async def test_asgi_query_params():
    """Test ASGI request with query parameters."""
    app = HttpResolverAlpha()

    @app.get("/search")
    def search():
        q = app.current_event.get_query_string_value("q", "")
        return {"query": q}

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/search",
        "query_string": b"q=python",
        "headers": [],
    }

    response_body = b""

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        nonlocal response_body
        if message["type"] == "http.response.body":
            response_body = message["body"]

    await app(scope, receive, send)

    body = json.loads(response_body)
    assert body["query"] == "python"


# =============================================================================
# HttpResolver Async Handler Tests
# =============================================================================


@pytest.mark.asyncio
async def test_async_handler():
    """Test async route handler."""
    app = HttpResolverAlpha()

    @app.get("/async")
    async def async_handler():
        await asyncio.sleep(0.001)
        return {"async": True}

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/async",
        "query_string": b"",
        "headers": [],
    }

    response_body = b""
    status_code = None

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        nonlocal response_body, status_code
        if message["type"] == "http.response.start":
            status_code = message["status"]
        elif message["type"] == "http.response.body":
            response_body = message["body"]

    await app(scope, receive, send)

    assert status_code == 200
    body = json.loads(response_body)
    assert body["async"] is True


@pytest.mark.asyncio
async def test_async_handler_with_path_params():
    """Test async handler with path parameters."""
    app = HttpResolverAlpha()

    @app.get("/users/<user_id>")
    async def get_user(user_id: str):
        await asyncio.sleep(0.001)
        return {"user_id": user_id, "async": True}

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/users/456",
        "query_string": b"",
        "headers": [],
    }

    response_body = b""

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        nonlocal response_body
        if message["type"] == "http.response.body":
            response_body = message["body"]

    await app(scope, receive, send)

    body = json.loads(response_body)
    assert body["user_id"] == "456"
    assert body["async"] is True


@pytest.mark.asyncio
async def test_async_handler_with_validation():
    """Test async handler with Pydantic validation."""
    app = HttpResolverAlpha(enable_validation=True)

    @app.post("/users")
    async def create_user(user: UserModel) -> UserResponse:
        await asyncio.sleep(0.001)
        return UserResponse(id="async-123", user=user)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/users",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
    }

    request_body = b'{"name": "AsyncUser", "age": 25}'
    response_body = b""
    status_code = None

    async def receive():
        return {"type": "http.request", "body": request_body, "more_body": False}

    async def send(message):
        nonlocal response_body, status_code
        if message["type"] == "http.response.start":
            status_code = message["status"]
        elif message["type"] == "http.response.body":
            response_body = message["body"]

    await app(scope, receive, send)

    assert status_code == 200
    body = json.loads(response_body)
    assert body["id"] == "async-123"
    assert body["user"]["name"] == "AsyncUser"


@pytest.mark.asyncio
async def test_sync_handler_in_async_context():
    """Test sync handler works in ASGI async context."""
    app = HttpResolverAlpha()

    @app.get("/sync")
    def sync_handler():
        return {"sync": True}

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/sync",
        "query_string": b"",
        "headers": [],
    }

    response_body = b""

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        nonlocal response_body
        if message["type"] == "http.response.body":
            response_body = message["body"]

    await app(scope, receive, send)

    body = json.loads(response_body)
    assert body["sync"] is True


@pytest.mark.asyncio
async def test_mixed_sync_async_handlers():
    """Test app with both sync and async handlers."""
    app = HttpResolverAlpha()

    @app.get("/sync")
    def sync_handler():
        return {"type": "sync"}

    @app.get("/async")
    async def async_handler():
        await asyncio.sleep(0.001)
        return {"type": "async"}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    # Test sync handler
    sync_body = b""

    async def send_sync(message):
        nonlocal sync_body
        if message["type"] == "http.response.body":
            sync_body = message["body"]

    await app(
        {"type": "http", "method": "GET", "path": "/sync", "query_string": b"", "headers": []},
        receive,
        send_sync,
    )

    # Test async handler
    async_body = b""

    async def send_async(message):
        nonlocal async_body
        if message["type"] == "http.response.body":
            async_body = message["body"]

    await app(
        {"type": "http", "method": "GET", "path": "/async", "query_string": b"", "headers": []},
        receive,
        send_async,
    )

    assert json.loads(sync_body)["type"] == "sync"
    assert json.loads(async_body)["type"] == "async"


# =============================================================================
# HttpResolver OpenAPI Tests
# =============================================================================


def test_openapi_schema_generation():
    """Test OpenAPI schema is generated correctly."""
    app = HttpResolverAlpha(enable_validation=True)

    @app.get("/users/<user_id>")
    def get_user(user_id: str) -> dict:
        return {"user_id": user_id}

    @app.post("/users")
    def create_user(user: UserModel) -> UserResponse:
        return UserResponse(id="123", user=user)

    schema = app.get_openapi_schema(
        title="Test API",
        version="1.0.0",
    )

    assert schema.info.title == "Test API"
    assert schema.info.version == "1.0.0"
    assert "/users/{user_id}" in schema.paths
    assert "/users" in schema.paths


def test_openapi_schema_includes_validation_errors():
    """Test OpenAPI schema includes 422 validation error responses."""
    app = HttpResolverAlpha(enable_validation=True)

    @app.post("/users")
    def create_user(user: UserModel) -> UserResponse:
        return UserResponse(id="123", user=user)

    schema = app.get_openapi_schema(title="Test API", version="1.0.0")

    post_operation = schema.paths["/users"].post
    assert 422 in post_operation.responses


# =============================================================================
# MockLambdaContext Tests
# =============================================================================


def test_mock_lambda_context_attributes():
    """Test MockLambdaContext has required attributes."""
    ctx = MockLambdaContext()

    assert ctx.function_name == "http-resolver"
    assert ctx.memory_limit_in_mb == 128
    assert "arn:aws:lambda" in ctx.invoked_function_arn
    assert ctx.aws_request_id is not None
    assert ctx.get_remaining_time_in_millis() > 0
