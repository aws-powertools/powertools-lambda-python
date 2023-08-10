from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, Response
from aws_lambda_powertools.event_handler.middlewares import SchemaValidationMiddleware
from tests.functional.utils import load_event


def test_pass_schema_validation(validation_schema):
    # GIVEN
    app = ApiGatewayResolver()

    @app.post("/my/path", middlewares=[SchemaValidationMiddleware(validation_schema)])
    def post_lambda() -> Response:
        return Response(200, content_types.TEXT_HTML, "path")

    # WHEN calling the event handler
    result = app(load_event("apigatewayeSchemaMiddlwareValidEvent.json"), {})

    # THEN
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.TEXT_HTML]
    assert result["body"] == "path"


def test_fail_schema_validation(validation_schema):
    # GIVEN
    app = ApiGatewayResolver()

    @app.post("/my/path", middlewares=[SchemaValidationMiddleware(validation_schema)])
    def post_lambda() -> Response:
        return Response(200, content_types.TEXT_HTML, "Should not be returned")

    # WHEN calling the event handler
    result = app(load_event("apigatewayeSchemaMiddlwareInvalidEvent.json"), {})
    print(f"\nRESULT:::{result}")

    # THEN
    assert result["statusCode"] == 400
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    assert (
        result["body"]
        == "{\"message\": \"Bad Request: Failed schema validation. Error: data must contain ['message'] properties, Path: ['data'], Data: {'username': 'lessa'}\"}"  # noqa: E501
    )


def test_invalid_schema_validation():
    # GIVEN
    app = ApiGatewayResolver()

    @app.post("/my/path", middlewares=[SchemaValidationMiddleware(inbound_schema="schema.json")])
    def post_lambda() -> Response:
        return Response(200, content_types.TEXT_HTML, "Should not be returned")

    # WHEN calling the event handler
    result = app(load_event("apigatewayeSchemaMiddlwareValidEvent.json"), {})

    print(f"\nRESULT:::{result}")
    # THEN
    assert result["statusCode"] == 500
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    assert (
        result["body"]
        == "{\"message\": \"Schema received: schema.json, Formats: {}. Error: 'str' object has no attribute 'items'\"}"
    )
