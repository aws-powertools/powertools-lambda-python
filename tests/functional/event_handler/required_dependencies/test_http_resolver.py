"""Tests for HttpResolverLocal - ASGI-compatible HTTP resolver for local development."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from aws_lambda_powertools.event_handler import HttpResolverLocal, Response
from aws_lambda_powertools.event_handler.http_resolver import MockLambdaContext

# Suppress warning for all tests
pytestmark = pytest.mark.filterwarnings("ignore:HttpResolverLocal is intended for local development")


# =============================================================================
# ASGI Test Helpers
# =============================================================================


def make_asgi_receive(body: bytes = b""):
    """Create an ASGI receive callable."""

    async def receive() -> dict[str, Any]:
        await asyncio.sleep(0)  # Yield control to satisfy async requirement
        return {"type": "http.request", "body": body, "more_body": False}

    return receive


def make_asgi_send():
    """Create an ASGI send callable that captures response."""
    captured: dict[str, Any] = {"status_code": None, "body": b""}

    async def send(message: dict[str, Any]) -> None:
        await asyncio.sleep(0)  # Yield control to satisfy async requirement
        if message["type"] == "http.response.start":
            captured["status_code"] = message["status"]
        elif message["type"] == "http.response.body":
            captured["body"] = message["body"]

    return send, captured


# =============================================================================
# Basic Routing Tests
# =============================================================================


def test_simple_get_route():
    # GIVEN a simple GET route
    app = HttpResolverLocal()

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
    app = HttpResolverLocal()

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
    app = HttpResolverLocal()

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
    app = HttpResolverLocal()

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
    app = HttpResolverLocal()

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
    app = HttpResolverLocal()

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
    app = HttpResolverLocal()

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
    app = HttpResolverLocal()
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
    app = HttpResolverLocal()

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
    app = HttpResolverLocal()
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
    app = HttpResolverLocal()
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
    app = HttpResolverLocal()
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
    app = HttpResolverLocal()

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
    app = HttpResolverLocal()

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

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN it returns the expected response
    assert captured["status_code"] == 200
    body = json.loads(captured["body"])
    assert body["message"] == "Hello, World!"


@pytest.mark.asyncio
async def test_asgi_custom_not_found():
    # GIVEN an app with custom not_found handler
    app = HttpResolverLocal()

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

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    # WHEN requesting unknown route via ASGI
    await app(scope, receive, send)

    # THEN custom handler is called
    assert captured["status_code"] == 404
    body = json.loads(captured["body"])
    assert body["error"] == "Custom 404"
    assert body["path"] == "/unknown-asgi-route"


@pytest.mark.asyncio
async def test_asgi_post_request():
    # GIVEN an app with a POST route
    app = HttpResolverLocal()

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

    receive = make_asgi_receive(b'{"name": "John"}')
    send, captured = make_asgi_send()

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN it parses the body correctly
    assert captured["status_code"] == 200
    body = json.loads(captured["body"])
    assert body["created"] is True
    assert body["name"] == "John"


@pytest.mark.asyncio
async def test_asgi_query_params():
    # GIVEN an app with a route that reads query params
    app = HttpResolverLocal()

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

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN it extracts query params correctly
    body = json.loads(captured["body"])
    assert body["query"] == "python"


# =============================================================================
# Async Handler Tests
# =============================================================================


@pytest.mark.asyncio
async def test_async_handler():
    # GIVEN an app with an async handler
    app = HttpResolverLocal()

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

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN async handler executes correctly
    assert captured["status_code"] == 200
    body = json.loads(captured["body"])
    assert body["async"] is True


@pytest.mark.asyncio
async def test_async_handler_with_path_params():
    # GIVEN an app with async handler and path params
    app = HttpResolverLocal()

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

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN path params are extracted correctly
    body = json.loads(captured["body"])
    assert body["user_id"] == "456"
    assert body["async"] is True


@pytest.mark.asyncio
async def test_sync_handler_in_async_context():
    # GIVEN an app with a sync handler
    app = HttpResolverLocal()

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

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN sync handler works in async context
    body = json.loads(captured["body"])
    assert body["sync"] is True


@pytest.mark.asyncio
async def test_mixed_sync_async_handlers():
    # GIVEN an app with both sync and async handlers
    app = HttpResolverLocal()

    @app.get("/sync")
    def sync_handler():
        return {"type": "sync"}

    @app.get("/async")
    async def async_handler():
        await asyncio.sleep(0.001)
        return {"type": "async"}

    receive = make_asgi_receive()

    # WHEN calling sync handler
    send_sync, captured_sync = make_asgi_send()
    await app(
        {"type": "http", "method": "GET", "path": "/sync", "query_string": b"", "headers": []},
        receive,
        send_sync,
    )

    # WHEN calling async handler
    send_async, captured_async = make_asgi_send()
    await app(
        {"type": "http", "method": "GET", "path": "/async", "query_string": b"", "headers": []},
        receive,
        send_async,
    )

    # THEN both work correctly
    assert json.loads(captured_sync["body"])["type"] == "sync"
    assert json.loads(captured_async["body"])["type"] == "async"


# =============================================================================
# Exception Handler Tests
# =============================================================================


def test_exception_handler():
    # GIVEN an app with a custom exception handler
    app = HttpResolverLocal()

    class CustomError(Exception):
        pass

    @app.exception_handler(CustomError)
    def handle_custom_error(exc: CustomError):
        return Response(
            status_code=400,
            content_type="application/json",
            body={"error": "Custom error handled"},
        )

    @app.get("/error")
    def raise_error():
        raise CustomError("Something went wrong")

    event = {
        "httpMethod": "GET",
        "path": "/error",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    # WHEN the route raises the exception
    result = app.resolve(event, MockLambdaContext())

    # THEN the custom handler catches it
    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert body["error"] == "Custom error handled"


@pytest.mark.asyncio
async def test_async_exception_handler():
    # GIVEN an app with exception handler and async route
    app = HttpResolverLocal()

    class CustomError(Exception):
        pass

    @app.exception_handler(CustomError)
    def handle_custom_error(exc: CustomError):
        return Response(
            status_code=400,
            content_type="application/json",
            body={"error": "Async error handled"},
        )

    @app.get("/error")
    async def raise_error():
        await asyncio.sleep(0.001)
        raise CustomError("Async error")

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/error",
        "query_string": b"",
        "headers": [],
    }

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    # WHEN the async route raises the exception
    await app(scope, receive, send)

    # THEN the exception handler catches it
    assert captured["status_code"] == 400
    body = json.loads(captured["body"])
    assert body["error"] == "Async error handled"


# =============================================================================
# ASGI Lifespan Tests
# =============================================================================


@pytest.mark.asyncio
async def test_asgi_lifespan_startup_shutdown():
    # GIVEN an app
    app = HttpResolverLocal()

    @app.get("/hello")
    def hello():
        return {"message": "Hello"}

    scope = {"type": "lifespan"}
    messages_received: list[str] = []
    messages_sent: list[str] = []

    async def receive() -> dict[str, Any]:
        await asyncio.sleep(0)
        if not messages_received:
            messages_received.append("startup")
            return {"type": "lifespan.startup"}
        else:
            messages_received.append("shutdown")
            return {"type": "lifespan.shutdown"}

    async def send(message: dict[str, Any]) -> None:
        await asyncio.sleep(0)
        messages_sent.append(message["type"])

    # WHEN handling lifespan events
    await app(scope, receive, send)

    # THEN startup and shutdown are handled
    assert "lifespan.startup.complete" in messages_sent
    assert "lifespan.shutdown.complete" in messages_sent


@pytest.mark.asyncio
async def test_asgi_ignores_non_http_scope():
    # GIVEN an app
    app = HttpResolverLocal()

    @app.get("/hello")
    def hello():
        return {"message": "Hello"}

    scope = {"type": "websocket"}  # Not HTTP
    send_called = False

    async def receive() -> dict[str, Any]:
        await asyncio.sleep(0)
        return {"type": "websocket.connect"}

    async def send(message: dict[str, Any]) -> None:
        nonlocal send_called
        await asyncio.sleep(0)
        send_called = True

    # WHEN handling non-HTTP scope
    await app(scope, receive, send)

    # THEN nothing is sent (early return)
    assert send_called is False


@pytest.mark.asyncio
async def test_asgi_binary_response():
    # GIVEN an app that returns binary data (bytes body is auto base64 encoded)
    app = HttpResolverLocal()
    binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00"  # PNG header bytes

    @app.get("/image")
    def get_image():
        # When body is bytes, Response auto base64 encodes it
        return Response(
            status_code=200,
            content_type="image/png",
            body=binary_data,
        )

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/image",
        "query_string": b"",
        "headers": [],
    }

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN it decodes base64 and returns binary data
    assert captured["status_code"] == 200
    assert captured["body"] == binary_data


@pytest.mark.asyncio
async def test_asgi_duplicate_headers():
    # GIVEN an ASGI request with duplicate headers
    app = HttpResolverLocal()

    @app.get("/headers")
    def get_headers():
        # Return the accept header which has duplicates
        accept = app.current_event.headers.get("accept", "")
        return {"accept": accept}

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/headers",
        "query_string": b"",
        "headers": [
            (b"accept", b"text/html"),
            (b"accept", b"application/json"),  # Duplicate header
        ],
    }

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN duplicate headers are joined with comma
    assert captured["status_code"] == 200
    body = json.loads(captured["body"])
    assert body["accept"] == "text/html, application/json"


@pytest.mark.asyncio
async def test_asgi_with_cookies():
    # GIVEN an app that sets cookies
    from aws_lambda_powertools.shared.cookies import Cookie

    app = HttpResolverLocal()

    @app.get("/set-cookie")
    def set_cookie():
        cookie = Cookie(name="session", value="abc123")
        return Response(
            status_code=200,
            content_type="application/json",
            body={"message": "Cookie set"},
            cookies=[cookie],
        )

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/set-cookie",
        "query_string": b"",
        "headers": [],
    }

    receive = make_asgi_receive()
    captured_headers: list[tuple[bytes, bytes]] = []

    async def send(message: dict[str, Any]) -> None:
        await asyncio.sleep(0)
        if message["type"] == "http.response.start":
            captured_headers.extend(message.get("headers", []))

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN Set-Cookie header is present
    cookie_headers = [h for h in captured_headers if h[0] == b"set-cookie"]
    assert len(cookie_headers) == 1
    assert b"session=abc123" in cookie_headers[0][1]


@pytest.mark.asyncio
async def test_async_middleware():
    # GIVEN an app with async middleware
    app = HttpResolverLocal()
    order: list[str] = []

    async def async_middleware(app, next_middleware):
        order.append("async_before")
        await asyncio.sleep(0.001)
        response = await next_middleware(app)
        order.append("async_after")
        return response

    app.use([async_middleware])

    @app.get("/test")
    async def test_route():
        order.append("handler")
        return {"ok": True}

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "headers": [],
    }

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN async middleware executes correctly
    assert captured["status_code"] == 200
    assert order == ["async_before", "handler", "async_after"]


def test_unhandled_exception_raises():
    # GIVEN an app without exception handler for ValueError
    app = HttpResolverLocal()

    @app.get("/error")
    def raise_error():
        raise ValueError("Unhandled error")

    event = {
        "httpMethod": "GET",
        "path": "/error",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    # WHEN the route raises an unhandled exception
    # THEN it propagates up
    with pytest.raises(ValueError, match="Unhandled error"):
        app.resolve(event, MockLambdaContext())


def test_default_not_found_without_custom_handler():
    # GIVEN an app WITHOUT custom not_found handler
    app = HttpResolverLocal()

    @app.get("/exists")
    def exists():
        return {"exists": True}

    event = {
        "httpMethod": "GET",
        "path": "/unknown",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    # WHEN requesting unknown route
    result = app.resolve(event, MockLambdaContext())

    # THEN default 404 response is returned
    assert result["statusCode"] == 404
    body = json.loads(result["body"])
    assert body["message"] == "Not found"


def test_method_not_matching_continues_search():
    # GIVEN an app with routes for different methods on same path
    app = HttpResolverLocal()

    @app.get("/resource")
    def get_resource():
        return {"method": "GET"}

    @app.post("/resource")
    def post_resource():
        return {"method": "POST"}

    # WHEN requesting with POST
    event = {
        "httpMethod": "POST",
        "path": "/resource",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }
    result = app.resolve(event, MockLambdaContext())

    # THEN it finds the POST handler (skipping GET)
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["method"] == "POST"


def test_list_headers_serialization():
    # GIVEN an app that returns list headers
    app = HttpResolverLocal()

    @app.get("/multi-header")
    def multi_header():
        return Response(
            status_code=200,
            content_type="application/json",
            body={"ok": True},
            headers={"X-Custom": ["value1", "value2"]},
        )

    event = {
        "httpMethod": "GET",
        "path": "/multi-header",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    # WHEN the route is resolved
    result = app.resolve(event, MockLambdaContext())

    # THEN list headers are joined with comma
    assert result["statusCode"] == 200
    assert result["headers"]["X-Custom"] == "value1, value2"


def test_string_body_in_event():
    # GIVEN an event with string body (not bytes)
    app = HttpResolverLocal()

    @app.post("/echo")
    def echo():
        return {"body": app.current_event.body}

    # Body is already a string, not bytes
    event = {
        "httpMethod": "POST",
        "path": "/echo",
        "headers": {"content-type": "text/plain"},
        "queryStringParameters": {},
        "body": "plain text body",
    }

    # WHEN the route is resolved
    result = app.resolve(event, MockLambdaContext())

    # THEN string body is handled correctly
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["body"] == "plain text body"


@pytest.mark.asyncio
async def test_asgi_default_not_found():
    # GIVEN an app WITHOUT custom not_found handler
    app = HttpResolverLocal()

    @app.get("/exists")
    def exists():
        return {"exists": True}

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/unknown-route",
        "query_string": b"",
        "headers": [],
    }

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    # WHEN requesting unknown route via ASGI
    await app(scope, receive, send)

    # THEN default 404 is returned
    assert captured["status_code"] == 404
    body = json.loads(captured["body"])
    assert body["message"] == "Not found"


@pytest.mark.asyncio
async def test_asgi_unhandled_exception_raises():
    # GIVEN an app without exception handler for ValueError
    app = HttpResolverLocal()

    @app.get("/error")
    async def raise_error():
        raise ValueError("Async unhandled error")

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/error",
        "query_string": b"",
        "headers": [],
    }

    receive = make_asgi_receive()
    send, _ = make_asgi_send()

    # WHEN the route raises an unhandled exception
    # THEN it propagates up
    with pytest.raises(ValueError, match="Async unhandled error"):
        await app(scope, receive, send)


@pytest.mark.asyncio
async def test_asgi_wrong_method_returns_not_found():
    # GIVEN an app with only a GET route
    app = HttpResolverLocal()

    @app.get("/hello")
    def hello():
        return {"message": "Hello"}

    # WHEN calling with POST method (route exists but method doesn't match)
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/hello",
        "query_string": b"",
        "headers": [],
    }

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    await app(scope, receive, send)

    # THEN it returns 404 (method mismatch is treated as not found)
    assert captured["status_code"] == 404


# =============================================================================
# CORS Tests (issue #8267)
# =============================================================================


@pytest.mark.asyncio
async def test_cors_options_preflight_returns_204():
    # GIVEN an app with CORSConfig and a POST route
    from aws_lambda_powertools.event_handler.api_gateway import CORSConfig

    app = HttpResolverLocal(cors=CORSConfig(allow_origin="*"))

    @app.post("/items")
    def create_item():
        return {"ok": True}

    # WHEN a browser sends a CORS preflight OPTIONS request
    scope = {
        "type": "http",
        "method": "OPTIONS",
        "path": "/items",
        "query_string": b"",
        "headers": [
            (b"origin", b"http://localhost:3000"),
            (b"access-control-request-method", b"POST"),
        ],
    }

    receive = make_asgi_receive()
    captured: dict[str, Any] = {"status_code": None, "headers": []}

    async def send(message: dict[str, Any]) -> None:
        await asyncio.sleep(0)
        if message["type"] == "http.response.start":
            captured["status_code"] = message["status"]
            captured["headers"].extend(message.get("headers", []))

    await app(scope, receive, send)

    # THEN it returns 204 with CORS headers (not 500 or 404)
    assert captured["status_code"] == 204

    header_names = [name.lower() for name, _ in captured["headers"]]
    assert b"access-control-allow-origin" in header_names
    assert b"access-control-allow-methods" in header_names


@pytest.mark.asyncio
async def test_cors_options_preflight_with_exception_handler_does_not_return_500():
    # GIVEN an app with CORSConfig and a generic exception handler that returns 500
    import json

    from aws_lambda_powertools.event_handler.api_gateway import CORSConfig

    app = HttpResolverLocal(cors=CORSConfig(allow_origin="*"))

    @app.post("/items")
    def create_item():
        return {"ok": True}

    @app.exception_handler(Exception)
    def handle_server_error(ex: Exception):
        return Response(
            status_code=500,
            content_type="application/json",
            body=json.dumps({"error": "internal"}),
        )

    # WHEN a browser sends a CORS preflight OPTIONS request
    scope = {
        "type": "http",
        "method": "OPTIONS",
        "path": "/items",
        "query_string": b"",
        "headers": [
            (b"origin", b"http://localhost:3000"),
            (b"access-control-request-method", b"POST"),
        ],
    }

    receive = make_asgi_receive()
    captured: dict[str, Any] = {"status_code": None, "headers": []}

    async def send(message: dict[str, Any]) -> None:
        await asyncio.sleep(0)
        if message["type"] == "http.response.start":
            captured["status_code"] = message["status"]
            captured["headers"].extend(message.get("headers", []))

    await app(scope, receive, send)

    # THEN the OPTIONS request returns 204, not 500
    assert captured["status_code"] == 204
    header_names = [name.lower() for name, _ in captured["headers"]]
    assert b"access-control-allow-origin" in header_names


@pytest.mark.asyncio
async def test_no_cors_options_returns_404():
    # GIVEN an app WITHOUT CORSConfig
    app = HttpResolverLocal()

    @app.post("/items")
    def create_item():
        return {"ok": True}

    # WHEN a browser sends an OPTIONS request (no CORS configured)
    scope = {
        "type": "http",
        "method": "OPTIONS",
        "path": "/items",
        "query_string": b"",
        "headers": [],
    }

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    await app(scope, receive, send)

    # THEN it returns 404 (no CORS config, no special handling)
    assert captured["status_code"] == 404


@pytest.mark.asyncio
async def test_cors_options_includes_allowed_methods_header():
    # GIVEN an app with CORSConfig and multiple routes
    from aws_lambda_powertools.event_handler.api_gateway import CORSConfig

    app = HttpResolverLocal(cors=CORSConfig(allow_origin="https://example.com"))

    @app.get("/resource")
    def get_resource():
        return {"method": "GET"}

    @app.post("/resource")
    def post_resource():
        return {"method": "POST"}

    # WHEN an OPTIONS preflight is sent
    scope = {
        "type": "http",
        "method": "OPTIONS",
        "path": "/resource",
        "query_string": b"",
        "headers": [
            (b"origin", b"https://example.com"),
            (b"access-control-request-method", b"GET"),
        ],
    }

    receive = make_asgi_receive()
    captured: dict[str, Any] = {"status_code": None, "headers": []}

    async def send(message: dict[str, Any]) -> None:
        await asyncio.sleep(0)
        if message["type"] == "http.response.start":
            captured["status_code"] = message["status"]
            captured["headers"].extend(message.get("headers", []))

    await app(scope, receive, send)

    # THEN 204 is returned with Access-Control-Allow-Methods header
    assert captured["status_code"] == 204
    allow_methods_headers = [v for name, v in captured["headers"] if name.lower() == b"access-control-allow-methods"]
    assert len(allow_methods_headers) == 1


@pytest.mark.asyncio
async def test_cors_disallowed_header_not_in_allow_headers():
    # GIVEN an app with CORSConfig that only allows specific headers
    from aws_lambda_powertools.event_handler.api_gateway import CORSConfig

    app = HttpResolverLocal(cors=CORSConfig(allow_origin="*", allow_headers=["X-Custom-Allowed"]))

    @app.post("/items")
    def create_item():
        return {"ok": True}

    # WHEN a preflight requests an unlisted header
    scope = {
        "type": "http",
        "method": "OPTIONS",
        "path": "/items",
        "query_string": b"",
        "headers": [
            (b"origin", b"http://localhost:3000"),
            (b"access-control-request-method", b"POST"),
            (b"access-control-request-headers", b"X-Not-Allowed"),
        ],
    }

    receive = make_asgi_receive()
    captured: dict[str, Any] = {"status_code": None, "headers": []}

    async def send(message: dict[str, Any]) -> None:
        await asyncio.sleep(0)
        if message["type"] == "http.response.start":
            captured["status_code"] = message["status"]
            captured["headers"].extend(message.get("headers", []))

    await app(scope, receive, send)

    # THEN the server still returns 204 (browser enforces the rejection, not the server)
    assert captured["status_code"] == 204

    # AND the unlisted header is absent from Access-Control-Allow-Headers
    allow_headers_value = next(
        (v.decode() for name, v in captured["headers"] if name.lower() == b"access-control-allow-headers"),
        "",
    )
    assert "X-Not-Allowed" not in allow_headers_value
    # AND the explicitly allowed header IS present
    assert "X-Custom-Allowed" in allow_headers_value
