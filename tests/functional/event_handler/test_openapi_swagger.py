import json
from copy import deepcopy
from typing import Dict

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from tests.functional.utils import load_event

LOAD_GW_EVENT = load_event("apiGatewayProxyEvent.json")


def test_openapi_swagger():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger()

    LOAD_GW_EVENT["path"] = "/swagger"

    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == ["text/html"]


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
    assert isinstance(json.loads(result["body"]), Dict)
    assert "OpenAPI JSON View" in result["body"]


def test_openapi_swagger_json_view_with_custom_path():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger(path="/fizzbuzz/foobar", title="OpenAPI JSON View")
    LOAD_GW_EVENT["path"] = "/fizzbuzz/foobar"
    LOAD_GW_EVENT["queryStringParameters"] = {"format": "json"}

    result = app(LOAD_GW_EVENT, {})

    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == ["application/json"]
    assert isinstance(json.loads(result["body"]), Dict)
    assert "OpenAPI JSON View" in result["body"]


def test_openapi_swagger_with_rest_api_default_stage():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger()

    event = deepcopy(LOAD_GW_EVENT)
    event["path"] = "/swagger"
    event["requestContext"]["stage"] = "$default"

    result = app(event, {})
    assert result["statusCode"] == 200
    assert "ui.specActions.updateUrl('/swagger?format=json')" in result["body"]


def test_openapi_swagger_with_rest_api_stage():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger()

    event = deepcopy(LOAD_GW_EVENT)
    event["path"] = "/swagger"
    event["requestContext"]["stage"] = "prod"
    event["requestContext"]["path"] = "/prod/swagger"

    result = app(event, {})
    assert result["statusCode"] == 200
    assert "ui.specActions.updateUrl('/prod/swagger?format=json')" in result["body"]
