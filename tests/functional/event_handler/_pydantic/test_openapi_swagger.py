from __future__ import annotations

import json
import warnings

import pytest
from pydantic import BaseModel, ConfigDict

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.swagger_ui import OAuth2Config
from tests.functional.utils import load_event

LOAD_GW_EVENT = load_event("apiGatewayProxyEvent.json")


def test_openapi_swagger():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger()

    LOAD_GW_EVENT["path"] = "/swagger"

    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == ["text/html"]


def test_openapi_swagger_compressed():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger(compress=True)
    LOAD_GW_EVENT["multiValueHeaders"] = {"Accept-Encoding": ["gzip, deflate, br"]}
    LOAD_GW_EVENT["path"] = "/swagger"
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert result["isBase64Encoded"]
    assert result["multiValueHeaders"]["Content-Type"] == ["text/html"]
    assert result["multiValueHeaders"]["Content-Encoding"] == ["gzip"]


def test_openapi_swagger_with_custom_base_url():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger(swagger_base_url="https://aws.amazon.com")

    LOAD_GW_EVENT["path"] = "/swagger"

    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == ["text/html"]

    assert "aws.amazon.com/swagger-ui.min.css" in result["body"]
    assert "aws.amazon.com/swagger-ui-bundle.min.js" in result["body"]


def test_openapi_swagger_with_custom_base_url_no_embedded_assets():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger(swagger_base_url="https://aws.amazon.com")

    # Try to load the CSS file
    LOAD_GW_EVENT["path"] = "/swagger.css"
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 404

    # Try to load the JS file
    LOAD_GW_EVENT["path"] = "/swagger.js"
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 404


def test_openapi_swagger_json_view_with_default_path():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger(title="OpenAPI JSON View")
    LOAD_GW_EVENT["path"] = "/swagger"
    LOAD_GW_EVENT["queryStringParameters"] = {"format": "json"}

    result = app(LOAD_GW_EVENT, {})

    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == ["application/json"]
    assert isinstance(json.loads(result["body"]), dict)
    assert "OpenAPI JSON View" in result["body"]


def test_openapi_swagger_json_view_with_custom_path():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger(path="/fizzbuzz/foobar", title="OpenAPI JSON View")
    LOAD_GW_EVENT["path"] = "/fizzbuzz/foobar"
    LOAD_GW_EVENT["queryStringParameters"] = {"format": "json"}

    result = app(LOAD_GW_EVENT, {})

    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == ["application/json"]
    assert isinstance(json.loads(result["body"]), dict)
    assert "OpenAPI JSON View" in result["body"]


def test_openapi_swagger_with_persist_authorization():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger(persist_authorization=True)

    event = load_event("apiGatewayProxyEvent.json")
    event["path"] = "/swagger"

    result = app(event, {})
    assert result["statusCode"] == 200
    assert "persistAuthorization: true" in result["body"]


def test_openapi_swagger_oauth2_without_powertools_dev():
    with pytest.raises(ValueError) as exc:
        OAuth2Config(app_name="OAuth2 app", client_id="client_id", client_secret="verysecret")

    assert "cannot use client_secret without POWERTOOLS_DEV mode" in str(exc.value)


def test_openapi_swagger_oauth2_with_powertools_dev(monkeypatch):
    monkeypatch.setenv("POWERTOOLS_DEV", "1")

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("default")

        OAuth2Config(app_name="OAuth2 app", client_id="client_id", client_secret="verysecret")

        assert str(w[-1].message) == (
            "OAuth2Config is using client_secret and POWERTOOLS_DEV is set. This reveals sensitive information. "
            "DO NOT USE THIS OUTSIDE LOCAL DEVELOPMENT"
        )

    monkeypatch.delenv("POWERTOOLS_DEV")


def test_openapi_swagger_schema_title_property():
    """Test that schema title property is correctly included in OpenAPI spec.

    This test ensures that when a Pydantic model has a custom title defined
    via ConfigDict, it is properly reflected in the OpenAPI schema.
    See: https://github.com/aws-powertools/powertools-lambda-python/issues/7670
    """
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger()

    @app.get("/todos")
    def get_todos() -> ToDoWithTitle:
        return ToDoWithTitle(task="test")

    event = load_event("apiGatewayProxyEvent.json")
    event["path"] = "/swagger"
    event["queryStringParameters"] = {"format": "json"}

    result = app(event, {})

    assert result["statusCode"] == 200
    body = json.loads(result["body"])

    # Verify the schema has the title property set
    assert "components" in body
    assert "schemas" in body["components"]
    assert "ToDoWithTitle" in body["components"]["schemas"]
    assert body["components"]["schemas"]["ToDoWithTitle"]["title"] == "todoTitle"


class ToDoWithTitle(BaseModel):
    """Model with custom title for testing schema title property."""

    model_config = ConfigDict(title="todoTitle")
    task: str
