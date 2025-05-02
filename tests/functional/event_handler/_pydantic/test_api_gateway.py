from __future__ import annotations

import json
from decimal import Decimal
from functools import partial

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


def test_api_gateway_resolver_numeric_value():
    # GIVEN a basic API Gateway resolver
    app = ApiGatewayResolver(deserializer=partial(json.loads, parse_float=Decimal))

    @app.post("/my/path")
    def test_handler():
        return app.current_event.json_body

    # WHEN calling the event handler
    event = {}
    event.update(LOAD_GW_EVENT)
    event["body"] = '{"amount": 2.2999999999999998}'
    event["httpMethod"] = "POST"

    result = app(event, {})
    # THEN process event correctly
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    assert result["body"] == '{"amount":"2.2999999999999998"}'
