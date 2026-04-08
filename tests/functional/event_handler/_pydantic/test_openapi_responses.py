from secrets import randbelow
from typing import Optional, Union

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


def test_openapi_response_with_headers():
    """Test that response headers are properly included in OpenAPI schema"""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get(
        "/",
        responses={
            200: {
                "description": "Successful Response",
                "headers": {
                    "X-Rate-Limit": {
                        "description": "Rate limit header",
                        "schema": {"type": "integer"},
                    },
                    "X-Custom-Header": {
                        "description": "Custom header",
                        "schema": {"type": "string"},
                        "examples": {"example1": "value1"},
                    },
                },
            },
        },
    )
    def handler():
        return {"message": "hello"}

    schema = app.get_openapi_schema()
    response_dict = schema.paths["/"].get.responses[200]

    # Verify headers are present
    assert "headers" in response_dict
    headers = response_dict["headers"]

    # Check X-Rate-Limit header
    assert "X-Rate-Limit" in headers
    assert headers["X-Rate-Limit"]["description"] == "Rate limit header"
    assert headers["X-Rate-Limit"]["schema"]["type"] == "integer"

    # Check X-Custom-Header with examples
    assert "X-Custom-Header" in headers
    assert headers["X-Custom-Header"]["description"] == "Custom header"
    assert headers["X-Custom-Header"]["schema"]["type"] == "string"
    assert headers["X-Custom-Header"]["examples"]["example1"] == "value1"


def test_openapi_response_with_links():
    """Test that response links are properly included in OpenAPI schema"""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get(
        "/users/{user_id}",
        responses={
            200: {
                "description": "User details",
                "links": {
                    "GetUserOrders": {
                        "operationId": "getUserOrders",
                        "parameters": {"userId": "$response.body#/id"},
                        "description": "Get orders for this user",
                    },
                },
            },
        },
    )
    def get_user(user_id: str):
        return {"id": user_id, "name": "John Doe"}

    schema = app.get_openapi_schema()
    response = schema.paths["/users/{user_id}"].get.responses[200]

    # Verify links are present
    links = response.links

    assert "GetUserOrders" in links
    assert links["GetUserOrders"].operationId == "getUserOrders"
    assert links["GetUserOrders"].parameters["userId"] == "$response.body#/id"
    assert links["GetUserOrders"].description == "Get orders for this user"


def test_openapi_response_examples_preserved_with_model():
    """Test that examples are preserved when using model in response content"""
    app = APIGatewayRestResolver(enable_validation=True)

    class UserResponse(BaseModel):
        id: int
        name: str
        email: Optional[str] = None

    @app.get(
        "/",
        responses={
            200: {
                "description": "User response",
                "content": {
                    "application/json": {
                        "model": UserResponse,
                        "examples": {
                            "example1": {
                                "summary": "Example 1",
                                "value": {"id": 1, "name": "John", "email": "john@example.com"},
                            },
                            "example2": {
                                "summary": "Example 2",
                                "value": {"id": 2, "name": "Jane"},
                            },
                        },
                    },
                },
            },
        },
    )
    def handler() -> UserResponse:
        return UserResponse(id=1, name="Test")

    schema = app.get_openapi_schema()
    content = schema.paths["/"].get.responses[200].content["application/json"]

    # Verify model schema is present
    assert content.schema_.ref == "#/components/schemas/UserResponse"

    # Verify examples are preserved
    examples = content.examples

    assert "example1" in examples
    assert examples["example1"].summary == "Example 1"
    assert examples["example1"].value["id"] == 1
    assert examples["example1"].value["name"] == "John"

    assert "example2" in examples
    assert examples["example2"].summary == "Example 2"
    assert examples["example2"].value["id"] == 2


def test_openapi_custom_status_code():
    # GIVEN a route with a custom status_code
    app = APIGatewayRestResolver(enable_validation=True)

    class Item(BaseModel):
        name: str

    @app.post("/items", status_code=201)
    def create_item() -> Item:
        return Item(name="test")

    # WHEN we retrieve the OpenAPI schema
    schema = app.get_openapi_schema()
    responses = schema.paths["/items"].post.responses

    # THEN the schema should use 201 as the success response code instead of 200
    assert 201 in responses
    assert responses[201].description == "Successful Response"
    assert 200 not in responses


def test_openapi_custom_status_code_with_description():
    # GIVEN a route with a custom status_code and response_description
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items", status_code=201, response_description="Item created")
    def create_item():
        return {"name": "test"}

    # WHEN we retrieve the OpenAPI schema
    schema = app.get_openapi_schema()
    responses = schema.paths["/items"].post.responses

    # THEN the schema should use 201 with the custom description
    assert 201 in responses
    assert responses[201].description == "Item created"
    assert 200 not in responses


def test_openapi_default_status_code():
    # GIVEN a route without a custom status_code
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/items")
    def get_items():
        return {"items": []}

    # WHEN we retrieve the OpenAPI schema
    schema = app.get_openapi_schema()
    responses = schema.paths["/items"].get.responses

    # THEN the schema should default to 200
    assert 200 in responses
    assert responses[200].description == "Successful Response"


def test_openapi_custom_status_code_all_methods():
    # GIVEN routes with custom status_code on different HTTP methods
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/items", status_code=201)
    def create():
        return {}

    @app.put("/items", status_code=204)
    def update():
        return {}

    @app.delete("/items", status_code=204)
    def delete():
        return {}

    @app.patch("/items", status_code=202)
    def patch():
        return {}

    # WHEN we retrieve the OpenAPI schema
    schema = app.get_openapi_schema()

    # THEN each method should have the correct custom status code
    assert 201 in schema.paths["/items"].post.responses
    assert 204 in schema.paths["/items"].put.responses
    assert 204 in schema.paths["/items"].delete.responses
    assert 202 in schema.paths["/items"].patch.responses
