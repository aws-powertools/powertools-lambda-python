from secrets import randbelow
from typing import Union

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response


def test_openapi_default_response():
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/")
    def handler():
        pass

    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses
    assert 200 in responses.keys()
    assert responses[200].description == "Successful Response"

    assert 422 in responses.keys()
    assert responses[422].description == "Validation Error"


def test_openapi_200_response_with_description():
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/", response_description="Custom response")
    def handler():
        return {"message": "hello world"}

    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses
    assert 200 in responses.keys()
    assert responses[200].description == "Custom response"

    assert 422 in responses.keys()
    assert responses[422].description == "Validation Error"


def test_openapi_200_custom_response():
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/", responses={202: {"description": "Custom response"}})
    def handler():
        return {"message": "hello world"}

    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses
    assert 202 in responses.keys()
    assert responses[202].description == "Custom response"

    assert 200 not in responses.keys()  # 200 was not added due to custom responses
    assert 422 in responses.keys()  # 422 is always added due to potential data validation errors


def test_openapi_422_default_response():
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/")
    def handler():
        return {"message": "hello world"}

    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses
    assert 422 in responses.keys()
    assert responses[422].description == "Validation Error"


def test_openapi_422_custom_response():
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/", responses={422: {"description": "Custom validation response"}})
    def handler():
        return {"message": "hello world"}

    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses
    assert 422 in responses.keys()
    assert responses[422].description == "Custom validation response"


def test_openapi_200_custom_schema():
    app = APIGatewayRestResolver(enable_validation=True)

    class User(BaseModel):
        pass

    @app.get(
        "/",
        responses={
            200: {
                "description": "Custom response",
                "content": {"application/json": {"schema": User.model_json_schema()}},
            },
        },
    )
    def handler():
        return {"message": "hello world"}

    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses
    assert 200 in responses.keys()

    assert responses[200].description == "Custom response"
    assert responses[200].content["application/json"].schema_.title == "User"


def test_openapi_union_response():
    app = APIGatewayRestResolver(enable_validation=True)

    class User(BaseModel):
        pass

    class Order(BaseModel):
        pass

    @app.get(
        "/",
        responses={
            200: {"description": "200 Response", "content": {"application/json": {"model": User}}},
            202: {"description": "202 Response", "content": {"application/json": {"model": Order}}},
        },
    )
    def handler() -> Response[Union[User, Order]]:
        if randbelow(2) > 0:
            return Response(status_code=200, body=User())
        else:
            return Response(status_code=202, body=Order())

    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses
    assert 200 in responses.keys()
    assert responses[200].description == "200 Response"
    assert responses[200].content["application/json"].schema_.ref == "#/components/schemas/User"

    assert 202 in responses.keys()
    assert responses[202].description == "202 Response"
    assert responses[202].content["application/json"].schema_.ref == "#/components/schemas/Order"


def test_openapi_union_partial_response():
    app = APIGatewayRestResolver(enable_validation=True)

    class User(BaseModel):
        pass

    class Order(BaseModel):
        pass

    @app.get(
        "/",
        responses={
            200: {"description": "200 Response"},
            202: {"description": "202 Response", "content": {"application/json": {"model": Order}}},
        },
    )
    def handler() -> Response[Union[User, Order]]:
        if randbelow(2) > 0:
            return Response(status_code=200, body=User())
        else:
            return Response(status_code=202, body=Order())

    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses
    assert 200 in responses.keys()
    assert responses[200].description == "200 Response"
    assert responses[200].content["application/json"].schema_.anyOf is not None

    assert 202 in responses.keys()
    assert responses[202].description == "202 Response"
    assert responses[202].content["application/json"].schema_.ref == "#/components/schemas/Order"


def test_openapi_route_with_custom_response_validation():
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/", custom_response_validation_http_code=418)
    def handler():
        return {"message": "hello world"}

    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses
    assert 418 in responses
    assert responses[418].description == "Response Validation Error"


def test_openapi_resolver_with_custom_response_validation():
    app = APIGatewayRestResolver(enable_validation=True, response_validation_error_http_code=418)

    @app.get("/")
    def handler():
        return {"message": "hello world"}

    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses
    assert 418 in responses
    assert responses[418].description == "Response Validation Error"


def test_openapi_route_and_resolver_with_custom_response_validation():
    app = APIGatewayRestResolver(enable_validation=True, response_validation_error_http_code=417)

    @app.get("/", custom_response_validation_http_code=418)
    def handler():
        return {"message": "hello world"}

    @app.get("/hi")
    def another_handler():
        return {"message": "hello world"}

    schema = app.get_openapi_schema()
    responses_with_route_response_validation = schema.paths["/"].get.responses
    responses_with_resolver_response_validation = schema.paths["/hi"].get.responses
    assert 418 in responses_with_route_response_validation
    assert 417 not in responses_with_route_response_validation
    assert responses_with_route_response_validation[418].description == "Response Validation Error"
    assert 417 in responses_with_resolver_response_validation
    assert 418 not in responses_with_resolver_response_validation
    assert responses_with_resolver_response_validation[417].description == "Response Validation Error"


def test_openapi_enable_validation_disabled():
    # GIVEN An API Gateway resolver without validation
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler():
        pass

    # WHEN we retrieve the OpenAPI schema for the application
    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses

    # THE the schema should include a 200 successful response
    # but not a 422 validation error response since validation is disabled
    assert 200 in responses.keys()
    assert responses[200].description == "Successful Response"
    assert 422 not in responses.keys()
