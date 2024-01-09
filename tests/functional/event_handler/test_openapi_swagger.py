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
