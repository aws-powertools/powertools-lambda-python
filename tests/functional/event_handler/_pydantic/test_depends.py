"""Tests for Depends() with OpenAPI schema generation and validation."""

import json
from typing import Annotated

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Depends
from aws_lambda_powertools.event_handler.request import Request
from tests.functional.utils import load_event

API_GW_V2_EVENT = load_event("apiGatewayProxyV2Event.json")


# --- Fixtures ---


class AppConfig(BaseModel):
    region: str = "us-east-1"
    debug: bool = False


def get_config() -> AppConfig:
    return AppConfig(region="eu-west-1", debug=True)


def get_tenant() -> str:
    return "tenant-abc"


# --- OpenAPI schema tests ---


def test_depends_excluded_from_openapi_schema():
    """Depends() parameters must NOT appear in the OpenAPI schema."""
    app = APIGatewayHttpResolver(enable_validation=True)

    @app.get("/orders")
    def handler(tenant: Annotated[str, Depends(get_tenant)], status: str = "active"):
        return {"tenant": tenant, "status": status}

    schema = app.get_openapi_schema()
    get_op = schema.paths["/orders"].get
    param_names = [p.name for p in (get_op.parameters or [])]

    assert "tenant" not in param_names
    assert "status" in param_names


def test_depends_with_pydantic_model_excluded_from_schema():
    """Depends() returning a Pydantic model must NOT appear as a body param in the schema."""
    app = APIGatewayHttpResolver(enable_validation=True)

    @app.get("/info")
    def handler(config: Annotated[AppConfig, Depends(get_config)]):
        return {"region": config.region}

    schema = app.get_openapi_schema()
    get_op = schema.paths["/info"].get
    param_names = [p.name for p in (get_op.parameters or [])]

    assert "config" not in param_names
    # Should have no request body either
    assert get_op.requestBody is None


def test_depends_nested_excluded_from_openapi_schema():
    """Nested Depends() parameters must NOT appear in the OpenAPI schema."""
    app = APIGatewayHttpResolver(enable_validation=True)

    def get_prefix() -> str:
        return "Hello"

    def get_greeting(prefix: Annotated[str, Depends(get_prefix)]) -> str:
        return f"{prefix}, world!"

    @app.get("/greet")
    def handler(greeting: Annotated[str, Depends(get_greeting)]):
        return {"greeting": greeting}

    schema = app.get_openapi_schema()
    get_op = schema.paths["/greet"].get
    param_names = [p.name for p in (get_op.parameters or [])]

    assert "greeting" not in param_names
    assert "prefix" not in param_names


# --- Validation + Depends integration tests ---


def test_depends_with_validation_resolves_and_validates():
    """Depends() values are injected alongside validated query params."""
    app = APIGatewayHttpResolver(enable_validation=True)

    @app.get("/orders")
    def handler(tenant: Annotated[str, Depends(get_tenant)], limit: int = 10):
        return {"tenant": tenant, "limit": limit}

    event = {**API_GW_V2_EVENT}
    event["rawPath"] = "/orders"
    event["requestContext"] = {
        **event["requestContext"],
        "http": {"method": "GET", "path": "/orders"},
    }
    event["queryStringParameters"] = {"limit": "5"}

    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["tenant"] == "tenant-abc"
    assert body["limit"] == 5


def test_depends_pydantic_model_with_validation():
    """Depends() returning a Pydantic model works with enable_validation."""
    app = APIGatewayHttpResolver(enable_validation=True)

    @app.get("/config")
    def handler(config: Annotated[AppConfig, Depends(get_config)]):
        return {"region": config.region, "debug": config.debug}

    event = {**API_GW_V2_EVENT}
    event["rawPath"] = "/config"
    event["requestContext"] = {
        **event["requestContext"],
        "http": {"method": "GET", "path": "/config"},
    }

    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["region"] == "eu-west-1"
    assert body["debug"] is True


def test_depends_with_request_and_validation():
    """Depends() with Request injection works alongside validation."""
    app = APIGatewayHttpResolver(enable_validation=True)

    def get_method(request: Request) -> str:
        return request.method

    @app.post("/my/path")
    def handler(method: Annotated[str, Depends(get_method)], name: str = "world"):
        return {"method": method, "name": name}

    event = {**API_GW_V2_EVENT, "queryStringParameters": {"name": "Lambda"}}
    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["method"] == "POST"
    assert body["name"] == "Lambda"


def test_depends_override_with_validation():
    """dependency_overrides works with enable_validation."""
    app = APIGatewayHttpResolver(enable_validation=True)

    @app.get("/orders")
    def handler(tenant: Annotated[str, Depends(get_tenant)]):
        return {"tenant": tenant}

    app.dependency_overrides[get_tenant] = lambda: "test-tenant"

    event = {**API_GW_V2_EVENT}
    event["rawPath"] = "/orders"
    event["requestContext"] = {
        **event["requestContext"],
        "http": {"method": "GET", "path": "/orders"},
    }

    result = app(event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"tenant": "test-tenant"}

    app.dependency_overrides.clear()


def test_depends_with_path_params_and_validation():
    """Depends() works with path parameters and validation."""
    app = APIGatewayHttpResolver(enable_validation=True)

    @app.get("/orders/<order_id>")
    def handler(order_id: str, tenant: Annotated[str, Depends(get_tenant)]):
        return {"order_id": order_id, "tenant": tenant}

    event = {**API_GW_V2_EVENT}
    event["rawPath"] = "/orders/abc-123"
    event["requestContext"] = {
        **event["requestContext"],
        "http": {"method": "GET", "path": "/orders/abc-123"},
    }

    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["order_id"] == "abc-123"
    assert body["tenant"] == "tenant-abc"


def test_depends_with_regular_params_and_validation():
    """Depends() works alongside regular handler parameters with validation."""
    app = APIGatewayHttpResolver(enable_validation=True)

    def get_greeting() -> str:
        return "hello"

    @app.post("/my/path")
    def handler(name: str = "world", greeting: Annotated[str, Depends(get_greeting)] = ""):
        return {"message": f"{greeting}, {name}!"}

    event = {**API_GW_V2_EVENT, "queryStringParameters": {"name": "Lambda"}}
    result = app(event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"message": "hello, Lambda!"}
