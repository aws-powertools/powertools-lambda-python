from __future__ import annotations

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import (
    ApiGatewayResolver,
    Response,
)
from aws_lambda_powertools.event_handler.openapi.exceptions import RequestValidationError
from tests.functional.utils import load_event

LOAD_GW_EVENT = load_event("apiGatewayProxyEvent.json")


def test_exception_handler_with_data_validation():
    # GIVEN a resolver with an exception handler defined for RequestValidationError
    app = ApiGatewayResolver(enable_validation=True)

    @app.exception_handler(RequestValidationError)
    def handle_validation_error(ex: RequestValidationError):
        return Response(
            status_code=422,
            content_type=content_types.TEXT_PLAIN,
            body=f"Invalid data. Number of errors: {len(ex.errors())}",
        )

    @app.get("/my/path")
    def get_lambda(param: int): ...

    # WHEN calling the event handler
    # AND a RequestValidationError is raised
    result = app(LOAD_GW_EVENT, {})

    # THEN call the exception_handler
    assert result["statusCode"] == 422
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.TEXT_PLAIN]
    assert result["body"] == "Invalid data. Number of errors: 1"


def test_exception_handler_with_data_validation_pydantic_response():
    # GIVEN a resolver with an exception handler defined for RequestValidationError
    app = ApiGatewayResolver(enable_validation=True)

    class Err(BaseModel):
        msg: str

    @app.exception_handler(RequestValidationError)
    def handle_validation_error(ex: RequestValidationError):
        return Response(
            status_code=422,
            content_type=content_types.APPLICATION_JSON,
            body=Err(msg=f"Invalid data. Number of errors: {len(ex.errors())}"),
        )

    @app.get("/my/path")
    def get_lambda(param: int): ...

    # WHEN calling the event handler
    # AND a RequestValidationError is raised
    result = app(LOAD_GW_EVENT, {})

    # THEN exception handler's pydantic response should be serialized correctly
    assert result["statusCode"] == 422
    assert result["body"] == '{"msg":"Invalid data. Number of errors: 1"}'


def test_data_validation_error():
    # GIVEN a resolver without an exception handler
    app = ApiGatewayResolver(enable_validation=True)

    @app.get("/my/path")
    def get_lambda(param: int): ...

    # WHEN calling the event handler
    # AND a RequestValidationError is raised
    result = app(LOAD_GW_EVENT, {})

    # THEN call the exception_handler
    assert result["statusCode"] == 422
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    assert "missing" in result["body"]


def test_route_custom_status_code_with_dict():
    # GIVEN a route with a custom status_code returning a dict
    app = ApiGatewayResolver(enable_validation=True)

    @app.post("/my/path", status_code=201)
    def create_item():
        return {"name": "test"}

    event = {"httpMethod": "POST", "path": "/my/path", "body": "{}"}

    # WHEN calling the event handler
    result = app(event, {})

    # THEN the response should use the route's custom status code
    assert result["statusCode"] == 201


def test_route_custom_status_code_tuple_override():
    # GIVEN a route with status_code=201 but handler returns a tuple with 202
    app = ApiGatewayResolver(enable_validation=True)

    @app.post("/my/path", status_code=201)
    def create_item():
        return {"name": "test"}, 202

    event = {"httpMethod": "POST", "path": "/my/path", "body": "{}"}

    # WHEN calling the event handler
    result = app(event, {})

    # THEN the tuple status code should override the route's status code
    assert result["statusCode"] == 202


def test_route_custom_status_code_response_object_override():
    # GIVEN a route with status_code=201 but handler returns a Response with 204
    app = ApiGatewayResolver(enable_validation=True)

    @app.post("/my/path", status_code=201)
    def create_item():
        return Response(status_code=204, content_type=content_types.APPLICATION_JSON, body="{}")

    event = {"httpMethod": "POST", "path": "/my/path", "body": "{}"}

    # WHEN calling the event handler
    result = app(event, {})

    # THEN the Response object's status code should take precedence
    assert result["statusCode"] == 204


def test_route_default_status_code_with_dict():
    # GIVEN a route without custom status_code returning a dict
    app = ApiGatewayResolver(enable_validation=True)

    @app.get("/my/path")
    def get_items():
        return {"items": []}

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN the response should default to 200
    assert result["statusCode"] == 200
