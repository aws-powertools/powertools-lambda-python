import json
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

    # Using our embedded assets
    assert "/swagger.css" in result["body"]
    assert "/swagger.js" in result["body"]


def test_openapi_embedded_js():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger()

    LOAD_GW_EVENT["path"] = "/swagger.js"

    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == ["text/javascript"]


def test_openapi_embedded_css():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger()

    LOAD_GW_EVENT["path"] = "/swagger.css"

    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == ["text/css"]


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


def test_openapi_swagger_with_enabled_download_spec():
    app = APIGatewayRestResolver(enable_validation=True)
    app.enable_swagger(enable_download_spec=True)
    LOAD_GW_EVENT["path"] = "/swagger.json"

    result = app(LOAD_GW_EVENT, {})

    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == ["application/json"]
    assert isinstance(json.loads(result["body"]), Dict)
