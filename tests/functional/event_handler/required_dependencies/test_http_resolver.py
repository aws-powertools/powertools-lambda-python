"""Tests for HttpResolverAlpha - ASGI-compatible HTTP resolver for local development."""

from __future__ import annotations

import asyncio
import json

import pytest

from aws_lambda_powertools.event_handler import HttpResolverAlpha, Response
from aws_lambda_powertools.event_handler.http_resolver import MockLambdaContext

# Suppress alpha warning for all tests
pytestmark = pytest.mark.filterwarnings("ignore:HttpResolverAlpha is an alpha feature")


# =============================================================================
# Basic Routing Tests
# =============================================================================


def test_simple_get_route():
    # GIVEN a simple GET route
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

    # WHEN the route is resolved
    result = app.resolve(event, MockLambdaContext())

    # THEN it returns 200 with the expected body
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["message"] == "Hello, World!"


def test_path_parameters():
    # GIVEN a route with path parameters
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

    # WHEN the route is resolved
    result = app.resolve(event, MockLambdaContext())

    # THEN it extracts the path parameter correctly
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["user_id"] == "123"


def test_post_with_body():
    # GIVEN a POST route that reads the body
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

    # WHEN the route is resolved
    result = app.resolve(event, MockLambdaContext())

    # THEN it parses the JSON body correctly
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["created"] is True
    assert body["name"] == "John"


def test_query_parameters():
    # GIVEN a route that reads query parameters
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

    # WHEN the route is resolved
    result = app.resolve(event, MockLambdaContext())

    # THEN it extracts query parameters correctly
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["query"] == "python"
    assert body["page"] == "2"


def test_custom_response():
    # GIVEN a route that returns a custom Response
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

    # WHEN the route is resolved
    result = app.resolve(event, MockLambdaContext())

    # THEN it returns the custom status code and headers
    assert result["statusCode"] == 201
    assert result["headers"]["X-Custom-Header"] == "value"


def test_not_found():
    # GIVEN an app with a defined route
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

    # WHEN requesting an unknown route
    result = app.resolve(event, MockLambdaContext())

    # THEN it returns 404
    assert result["statusCode"] == 404


def test_custom_not_found_handler():
    # GIVEN an app with a custom not_found handler
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

    # WHEN requesting an unknown route
    result = app.resolve(event, MockLambdaContext())

    # THEN it calls the custom handler
    assert result["statusCode"] == 404
    body = json.loads(result["body"])
    assert body["error"] == "Custom Not Found"
    assert body["path"] == "/unknown-route"


# =============================================================================
# Middleware Tests
# =============================================================================


def test_middleware_execution():
    # GIVEN an app with middleware
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

    # WHEN the route is resolved
    result = app.resolve(event, MockLambdaContext())

    # THEN middleware executes in correct order
    assert result["statusCode"] == 200
    assert middleware_called == ["before", "handler", "after"]


def test_middleware_can_short_circuit():
    # GIVEN an app with auth middleware
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

    # WHEN requesting without auth header
    event = {
        "httpMethod": "GET",
        "path": "/protected",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }
    result = app.resolve(event, MockLambdaContext())

    # THEN it returns 401
    assert result["statusCode"] == 401

    # WHEN requesting with auth header
    event["headers"] = {"authorization": "Bearer token"}
    result = app.resolve(event, MockLambdaContext())

    # THEN it returns 200
    assert result["statusCode"] == 200


def test_multiple_middlewares():
    # GIVEN an app with multiple middlewares
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

    # WHEN the route is resolved
    app.resolve(event, MockLambdaContext())

    # THEN middlewares execute in correct order (onion model)
    assert order == ["m1_before", "m2_before", "handler", "m2_after", "m1_after"]


def test_route_specific_middleware():
    # GIVEN an app with route-specific middleware
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

    # WHEN requesting route WITH middleware
    event_with = {
        "httpMethod": "GET",
        "path": "/with-middleware",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }
    result = app.resolve(event_with, MockLambdaContext())

    # THEN middleware is called
    assert result["statusCode"] == 200
    assert route_middleware_called == ["route_middleware"]

    # WHEN requesting route WITHOUT middleware
    route_middleware_called.clear()
    event_without = {
        "httpMethod": "GET",
        "path": "/without-middleware",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }
    result = app.resolve(event_without, MockLambdaContext())

    # THEN middleware is NOT called
    assert result["statusCode"] == 200
    assert route_middleware_called == []


def test_route_middleware_with_global_middleware():
    # GIVEN an app with both global and route-specific middleware
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

    # WHEN the route is resolved
    app.resolve(event, MockLambdaContext())

    # THEN global middleware runs first, then route middleware
    assert order == ["global_before", "route_before", "handler", "route_after", "global_after"]


def test_route_middleware_can_modify_response():
    # GIVEN an app with middleware that modifies response
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

    # WHEN the route is resolved
    result = app.resolve(event, MockLambdaContext())

    # THEN the response has the added header
    assert result["statusCode"] == 200
    assert result["headers"]["X-Custom-Header"] == "added-by-middleware"


# =============================================================================
# ASGI Tests
# =============================================================================


@pytest.mark.asyncio
async def test_asgi_get_request():
    # GIVEN an app with a GET route
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

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN it returns the expected response
    assert status_code == 200
    body = json.loads(response_body)
    assert body["message"] == "Hello, World!"


@pytest.mark.asyncio
async def test_asgi_custom_not_found():
    # GIVEN an app with custom not_found handler
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

    # WHEN requesting unknown route via ASGI
    await app(scope, receive, send)

    # THEN custom handler is called
    assert status_code == 404
    body = json.loads(response_body)
    assert body["error"] == "Custom 404"
    assert body["path"] == "/unknown-asgi-route"


@pytest.mark.asyncio
async def test_asgi_post_request():
    # GIVEN an app with a POST route
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

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN it parses the body correctly
    assert status_code == 200
    body = json.loads(response_body)
    assert body["created"] is True
    assert body["name"] == "John"


@pytest.mark.asyncio
async def test_asgi_query_params():
    # GIVEN an app with a route that reads query params
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

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN it extracts query params correctly
    body = json.loads(response_body)
    assert body["query"] == "python"


# =============================================================================
# Async Handler Tests
# =============================================================================


@pytest.mark.asyncio
async def test_async_handler():
    # GIVEN an app with an async handler
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

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN async handler executes correctly
    assert status_code == 200
    body = json.loads(response_body)
    assert body["async"] is True


@pytest.mark.asyncio
async def test_async_handler_with_path_params():
    # GIVEN an app with async handler and path params
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

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN path params are extracted correctly
    body = json.loads(response_body)
    assert body["user_id"] == "456"
    assert body["async"] is True


@pytest.mark.asyncio
async def test_sync_handler_in_async_context():
    # GIVEN an app with a sync handler
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

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN sync handler works in async context
    body = json.loads(response_body)
    assert body["sync"] is True


@pytest.mark.asyncio
async def test_mixed_sync_async_handlers():
    # GIVEN an app with both sync and async handlers
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

    # WHEN calling sync handler
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

    # WHEN calling async handler
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

    # THEN both work correctly
    assert json.loads(sync_body)["type"] == "sync"
    assert json.loads(async_body)["type"] == "async"
