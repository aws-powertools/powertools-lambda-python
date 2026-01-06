"""Tests for HttpResolverAlpha with Pydantic validation."""

from __future__ import annotations

import asyncio
import json
from typing import Annotated

import pytest
from pydantic import BaseModel, Field

from aws_lambda_powertools.event_handler import HttpResolverAlpha
from aws_lambda_powertools.event_handler.http_resolver import MockLambdaContext
from aws_lambda_powertools.event_handler.openapi.params import Query

# Suppress alpha warning for all tests
pytestmark = pytest.mark.filterwarnings("ignore:HttpResolverAlpha is an alpha feature")


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

    # WHEN sending a valid body
    result = app.resolve(event, MockLambdaContext())

    # THEN it returns 200 with validated data
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["id"] == "user-123"
    assert body["user"]["name"] == "John"


def test_invalid_body_validation():
    # GIVEN an app with validation enabled
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

    # WHEN sending an invalid body
    result = app.resolve(event, MockLambdaContext())

    # THEN it returns 422 with validation error
    assert result["statusCode"] == 422
    body = json.loads(result["body"])
    assert "detail" in body


def test_missing_required_field():
    # GIVEN an app with validation enabled
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

    # WHEN sending body with missing required field
    result = app.resolve(event, MockLambdaContext())

    # THEN it returns 422
    assert result["statusCode"] == 422


# =============================================================================
# Query Parameter Validation Tests
# =============================================================================


def test_query_param_validation():
    # GIVEN an app with validated query parameters
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

    # WHEN called via ASGI interface
    await app(scope, receive, send)

    # THEN validation works with async handler
    assert status_code == 200
    body = json.loads(response_body)
    assert body["id"] == "async-123"
    assert body["user"]["name"] == "AsyncUser"


# =============================================================================
# OpenAPI Tests
# =============================================================================


def test_openapi_schema_generation():
    # GIVEN an app with validation and multiple routes
    app = HttpResolverAlpha(enable_validation=True)

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
    app = HttpResolverAlpha(enable_validation=True)

    @app.post("/users")
    def create_user(user: UserModel) -> UserResponse:
        return UserResponse(id="123", user=user)

    # WHEN generating OpenAPI schema
    schema = app.get_openapi_schema(title="Test API", version="1.0.0")

    # THEN schema includes 422 response
    post_operation = schema.paths["/users"].post
    assert 422 in post_operation.responses
