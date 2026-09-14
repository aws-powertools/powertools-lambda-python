"""Tests for HttpResolverLocal with Pydantic validation."""

from __future__ import annotations

import asyncio
import json
from typing import Annotated, Any

import pytest
from pydantic import BaseModel, Field

from aws_lambda_powertools.event_handler import HttpResolverLocal
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.http_resolver import MockLambdaContext
from aws_lambda_powertools.event_handler.openapi.params import Query

# =============================================================================
# ASGI Test Helpers
# =============================================================================


def make_asgi_receive(body: bytes = b""):
    """Create an ASGI receive callable."""

    async def receive() -> dict[str, Any]:
        await asyncio.sleep(0)
        return {"type": "http.request", "body": body, "more_body": False}

    return receive


def make_asgi_send():
    """Create an ASGI send callable that captures response."""
    captured: dict[str, Any] = {"status_code": None, "body": b""}

    async def send(message: dict[str, Any]) -> None:
        await asyncio.sleep(0)
        if message["type"] == "http.response.start":
            captured["status_code"] = message["status"]
        elif message["type"] == "http.response.body":
            captured["body"] = message["body"]

    return send, captured


class UserModel(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    email: str | None = None


class UserResponse(BaseModel):
    id: str
    user: UserModel
    created: bool = True


# =============================================================================
# Body Validation Tests
# =============================================================================


def test_valid_body_validation():
    # GIVEN an app with validation enabled and a route expecting UserModel
    app = HttpResolverLocal(enable_validation=True)

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

    # WHEN sending a valid body
    result = app.resolve(event, MockLambdaContext())

    # THEN it returns 200 with validated data
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["id"] == "user-123"
    assert body["user"]["name"] == "John"


def test_invalid_body_validation():
    # GIVEN an app with validation enabled
    app = HttpResolverLocal(enable_validation=True)

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

    # WHEN sending an invalid body
    result = app.resolve(event, MockLambdaContext())

    # THEN it returns 422 with validation error
    assert result["statusCode"] == 422
    body = json.loads(result["body"])
    assert "detail" in body


def test_missing_required_field():
    # GIVEN an app with validation enabled
    app = HttpResolverLocal(enable_validation=True)

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

    # WHEN sending body with missing required field
    result = app.resolve(event, MockLambdaContext())

    # THEN it returns 422
    assert result["statusCode"] == 422


# =============================================================================
# Query Parameter Validation Tests
# =============================================================================


def test_query_param_validation():
    # GIVEN an app with validated query parameters
    app = HttpResolverLocal(enable_validation=True)

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

    # WHEN sending valid query params
    result = app.resolve(event, MockLambdaContext())

    # THEN it returns 200 with parsed values
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["query"] == "python"
    assert body["page"] == 2
    assert body["limit"] == 50


def test_invalid_query_param():
    # GIVEN an app with validated query parameters
    app = HttpResolverLocal(enable_validation=True)

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

    # WHEN sending invalid query param
    result = app.resolve(event, MockLambdaContext())

    # THEN it returns 422
    assert result["statusCode"] == 422


# =============================================================================
# Async Handler with Validation Tests
# =============================================================================


@pytest.mark.asyncio
async def test_async_handler_with_validation():
    # GIVEN an app with async handler and validation
    app = HttpResolverLocal(enable_validation=True)

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

    receive = make_asgi_receive(b'{"name": "AsyncUser", "age": 25}')
    send, captured = make_asgi_send()

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN validation works with async handler
    assert captured["status_code"] == 200
    body = json.loads(captured["body"])
    assert body["id"] == "async-123"
    assert body["user"]["name"] == "AsyncUser"


@pytest.mark.asyncio
async def test_async_handler_invalid_response_returns_422():
    # GIVEN an app with async handler and validation
    app = HttpResolverLocal(enable_validation=True)

    @app.get("/user")
    async def get_user() -> UserResponse:
        await asyncio.sleep(0.001)
        return {"name": "John"}  # type: ignore  # Missing required fields

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/user",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
    }

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN it returns 422 for invalid response
    assert captured["status_code"] == 422


@pytest.mark.asyncio
async def test_sync_handler_with_validation_via_asgi():
    # GIVEN an app with a sync handler and validation, called via ASGI
    app = HttpResolverLocal(enable_validation=True)

    @app.post("/users")
    def create_user(user: UserModel) -> UserResponse:
        return UserResponse(id="sync-123", user=user)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/users",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
    }

    receive = make_asgi_receive(b'{"name": "SyncUser", "age": 30}')
    send, captured = make_asgi_send()

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN validation works with sync handler
    assert captured["status_code"] == 200
    body = json.loads(captured["body"])
    assert body["id"] == "sync-123"
    assert body["user"]["name"] == "SyncUser"


@pytest.mark.asyncio
async def test_sync_handler_invalid_response_returns_422_via_asgi():
    # GIVEN an app with a sync handler and validation, called via ASGI
    app = HttpResolverLocal(enable_validation=True)

    @app.get("/user")
    def get_user() -> UserResponse:
        return {"name": "John"}  # type: ignore  # Missing required fields

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/user",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
    }

    receive = make_asgi_receive()
    send, captured = make_asgi_send()

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN it returns 422 for invalid response
    assert captured["status_code"] == 422


# =============================================================================
# OpenAPI Tests
# =============================================================================


def test_openapi_schema_generation():
    # GIVEN an app with validation and multiple routes
    app = HttpResolverLocal(enable_validation=True)

    @app.get("/users/<user_id>")
    def get_user(user_id: str) -> dict:
        return {"user_id": user_id}

    @app.post("/users")
    def create_user(user: UserModel) -> UserResponse:
        return UserResponse(id="123", user=user)

    # WHEN generating OpenAPI schema
    schema = app.get_openapi_schema(
        title="Test API",
        version="1.0.0",
    )

    # THEN schema contains all routes
    assert schema.info.title == "Test API"
    assert schema.info.version == "1.0.0"
    assert "/users/{user_id}" in schema.paths
    assert "/users" in schema.paths


def test_openapi_schema_includes_validation_errors():
    # GIVEN an app with validation
    app = HttpResolverLocal(enable_validation=True)

    @app.post("/users")
    def create_user(user: UserModel) -> UserResponse:
        return UserResponse(id="123", user=user)

    # WHEN generating OpenAPI schema
    schema = app.get_openapi_schema(title="Test API", version="1.0.0")

    # THEN schema includes 422 response
    post_operation = schema.paths["/users"].post
    assert 422 in post_operation.responses


async def _post_concurrent_request(app, name: str | None):
    payload = {} if name is None else {"name": name, "age": 30}
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/concurrent",
        "headers": [(b"content-type", b"application/json"), (b"x-request-name", (name or "invalid").encode())],
        "query_string": b"",
    }
    send, captured = make_asgi_send()
    await asyncio.wait_for(app(scope, make_asgi_receive(json.dumps(payload).encode()), send), timeout=5)
    return captured["status_code"], json.loads(captured["body"])


def test_concurrent_asgi_validation_preserves_each_request_body():
    # GIVEN one local application using native request validation
    app = HttpResolverLocal(enable_validation=True)

    @app.post("/concurrent")
    async def echo(user: UserModel) -> dict:
        await asyncio.sleep(0)
        return {"name": user.name}

    async def scenario():
        # WHEN distinct bodies are submitted concurrently
        return await asyncio.gather(*(_post_concurrent_request(app, str(i)) for i in range(6)))

    # THEN each caller receives its own input
    assert asyncio.run(scenario()) == [(200, {"name": str(i)}) for i in range(6)]


def _make_included_router_app():
    app = HttpResolverLocal(enable_validation=True)
    router = Router()

    @router.post("/concurrent")
    async def echo(user: UserModel) -> dict:
        app.append_context(name=user.name)
        await asyncio.sleep(0)
        return {
            "name": router.context["name"],
            "header": router.current_event.headers["x-request-name"],
            "request_id": router.lambda_context.aws_request_id,
        }

    app.include_router(router)
    return app


def test_asgi_included_router_uses_request_state():
    app = _make_included_router_app()

    assert asyncio.run(_post_concurrent_request(app, "one")) == (
        200,
        {"name": "one", "header": "one", "request_id": "local-request-id"},
    )


def test_concurrent_asgi_included_router_preserves_request_state():
    app = _make_included_router_app()

    async def scenario():
        return await asyncio.gather(*(_post_concurrent_request(app, str(i)) for i in range(6)))

    assert asyncio.run(scenario()) == [
        (200, {"name": str(i), "header": str(i), "request_id": "local-request-id"}) for i in range(6)
    ]


@pytest.mark.parametrize("interruption", ["invalid", "cancelled"])
def test_interrupted_asgi_request_does_not_clear_another_requests_state(interruption):
    async def scenario():
        # GIVEN an active request that reads its context after awaiting I/O
        app = HttpResolverLocal(enable_validation=True)
        entered = {name: asyncio.Event() for name in ("first", "second", "later")}
        release = {name: asyncio.Event() for name in entered}
        pending = []

        @app.post("/concurrent")
        async def echo(user: UserModel) -> dict:
            app.append_context(name=user.name)
            entered[user.name].set()
            await release[user.name].wait()
            return {"name": app.context["name"], "header": app.current_event.headers["x-request-name"]}

        async def start(name):
            task = asyncio.create_task(_post_concurrent_request(app, name))
            pending.append(task)
            await asyncio.wait_for(entered[name].wait(), timeout=5)
            return task

        try:
            first = await start("first")
            # WHEN another request fails validation or an overlapping request is cancelled
            if interruption == "invalid":
                status, _ = await _post_concurrent_request(app, None)
                assert status == 422
                survivor, name = first, "first"
            else:
                survivor, name = await start("second"), "second"
                first.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await first

            # THEN the surviving request retains both context and headers
            release[name].set()
            assert await survivor == (200, {"name": name, "header": name})
            release["later"].set()
            assert await _post_concurrent_request(app, "later") == (200, {"name": "later", "header": "later"})
        finally:
            for event in release.values():
                event.set()
            for task in pending:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

    asyncio.run(scenario())
