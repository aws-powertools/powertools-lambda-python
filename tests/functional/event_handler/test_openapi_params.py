from dataclasses import dataclass
from datetime import datetime
from typing import List

from pydantic import BaseModel

from aws_lambda_powertools.event_handler.api_gateway import APIGatewayRestResolver, Response, Router
from aws_lambda_powertools.event_handler.openapi.models import (
    Example,
    Parameter,
    ParameterInType,
    Schema,
)
from aws_lambda_powertools.event_handler.openapi.params import (
    Body,
    Param,
    ParamTypes,
    Query,
    _create_model_field,
    _Header,
)
from aws_lambda_powertools.shared.types import Annotated

JSON_CONTENT_TYPE = "application/json"


def test_openapi_no_params():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler():
        raise NotImplementedError()

    schema = app.get_openapi_schema()
    assert schema.info.title == "Powertools API"
    assert schema.info.version == "1.0.0"

    assert len(schema.paths.keys()) == 1
    assert "/" in schema.paths

    path = schema.paths["/"]
    assert path.get

    get = path.get
    assert get.summary == "GET /"
    assert get.operationId == "handler__get"

    assert get.responses is not None
    assert 200 in get.responses.keys()
    response = get.responses[200]
    assert response.description == "Successful Response"

    assert JSON_CONTENT_TYPE in response.content
    json_response = response.content[JSON_CONTENT_TYPE]
    assert json_response.schema_ == Schema()
    assert not json_response.examples
    assert not json_response.encoding


def test_openapi_with_scalar_params():
    app = APIGatewayRestResolver()

    @app.get("/users/<user_id>")
    def handler(user_id: str, include_extra: bool = False):
        raise NotImplementedError()

    schema = app.get_openapi_schema(title="My API", version="0.2.2")
    assert schema.info.title == "My API"
    assert schema.info.version == "0.2.2"

    assert len(schema.paths.keys()) == 1
    assert "/users/{user_id}" in schema.paths

    path = schema.paths["/users/{user_id}"]
    assert path.get

    get = path.get
    assert get.summary == "GET /users/{user_id}"
    assert get.operationId == "handler_users__user_id__get"
    assert len(get.parameters) == 2

    parameter = get.parameters[0]
    assert isinstance(parameter, Parameter)
    assert parameter.in_ == ParameterInType.path
    assert parameter.name == "user_id"
    assert parameter.required is True
    assert parameter.schema_.default is None
    assert parameter.schema_.type == "string"
    assert parameter.schema_.title == "User Id"

    parameter = get.parameters[1]
    assert isinstance(parameter, Parameter)
    assert parameter.in_ == ParameterInType.query
    assert parameter.name == "include_extra"
    assert parameter.required is False
    assert parameter.schema_.default is False
    assert parameter.schema_.type == "boolean"
    assert parameter.schema_.title == "Include Extra"


def test_openapi_with_custom_params():
    app = APIGatewayRestResolver()

    @app.get("/users", summary="Get Users", operation_id="GetUsers", description="Get paginated users", tags=["Users"])
    def handler(
        count: Annotated[
            int,
            Query(gt=0, lt=100, examples=[Example(summary="Example 1", value=10)]),
        ] = 1,
    ):
        print(count)
        raise NotImplementedError()

    schema = app.get_openapi_schema()

    get = schema.paths["/users"].get
    assert len(get.parameters) == 1
    assert get.summary == "Get Users"
    assert get.operationId == "GetUsers"
    assert get.description == "Get paginated users"
    assert get.tags == ["Users"]

    parameter = get.parameters[0]
    assert parameter.required is False
    assert parameter.name == "count"
    assert parameter.in_ == ParameterInType.query
    assert parameter.schema_.type == "integer"
    assert parameter.schema_.default == 1
    assert parameter.schema_.title == "Count"
    assert parameter.schema_.exclusiveMinimum == 0
    assert parameter.schema_.exclusiveMaximum == 100
    assert len(parameter.schema_.examples) == 1
    assert parameter.schema_.examples[0].summary == "Example 1"
    assert parameter.schema_.examples[0].value == 10


def test_openapi_with_scalar_returns():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler() -> str:
        return "Hello, world"

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    get = schema.paths["/"].get
    assert get.parameters is None

    response = get.responses[200].content[JSON_CONTENT_TYPE]
    assert response.schema_.title == "Return"
    assert response.schema_.type == "string"


def test_openapi_with_response_returns():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler() -> Response[Annotated[str, Body(title="Response title")]]:
        return Response(body="Hello, world", status_code=200)

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    get = schema.paths["/"].get
    assert get.parameters is None

    response = get.responses[200].content[JSON_CONTENT_TYPE]
    assert response.schema_.title == "Response title"
    assert response.schema_.type == "string"


def test_openapi_with_omitted_param():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler(page: Annotated[str, Query(include_in_schema=False)]):
        return page

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    get = schema.paths["/"].get
    assert get.parameters is None


def test_openapi_with_description():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler(page: Annotated[str, Query(description="This is a description")]):
        return page

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    get = schema.paths["/"].get
    assert len(get.parameters) == 1

    parameter = get.parameters[0]
    assert parameter.description == "This is a description"


def test_openapi_with_deprecated():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler(page: Annotated[str, Query(deprecated=True)]):
        return page

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    get = schema.paths["/"].get
    assert len(get.parameters) == 1

    parameter = get.parameters[0]
    assert parameter.deprecated is True


def test_openapi_with_pydantic_returns():
    app = APIGatewayRestResolver()

    class User(BaseModel):
        name: str

    @app.get("/")
    def handler() -> User:
        return User(name="Ruben Fonseca")

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    get = schema.paths["/"].get
    assert get.parameters is None

    response = get.responses[200].content[JSON_CONTENT_TYPE]
    reference = response.schema_
    assert reference.ref == "#/components/schemas/User"

    assert "User" in schema.components.schemas
    user_schema = schema.components.schemas["User"]
    assert isinstance(user_schema, Schema)
    assert user_schema.title == "User"
    assert "name" in user_schema.properties


def test_openapi_with_pydantic_nested_returns():
    app = APIGatewayRestResolver()

    class Order(BaseModel):
        date: datetime

    class User(BaseModel):
        name: str
        orders: List[Order]

    @app.get("/")
    def handler() -> User:
        return User(name="Ruben Fonseca", orders=[Order(date=datetime.now())])

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    assert "User" in schema.components.schemas
    assert "Order" in schema.components.schemas

    user_schema = schema.components.schemas["User"]
    assert "orders" in user_schema.properties
    assert user_schema.properties["orders"].type == "array"


def test_openapi_with_dataclass_return():
    app = APIGatewayRestResolver()

    @dataclass
    class User:
        surname: str

    @app.get("/")
    def handler() -> User:
        return User(surname="Fonseca")

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    get = schema.paths["/"].get
    assert get.parameters is None

    response = get.responses[200].content[JSON_CONTENT_TYPE]
    reference = response.schema_
    assert reference.ref == "#/components/schemas/User"

    assert "User" in schema.components.schemas
    user_schema = schema.components.schemas["User"]
    assert isinstance(user_schema, Schema)
    assert user_schema.title == "User"
    assert "surname" in user_schema.properties


def test_openapi_with_body_param():
    app = APIGatewayRestResolver()

    class User(BaseModel):
        name: str

    @app.post("/users")
    def handler(user: User):
        print(user)

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    post = schema.paths["/users"].post
    assert post.parameters is None
    assert post.requestBody is not None

    request_body = post.requestBody
    assert request_body.required is True
    assert request_body.content[JSON_CONTENT_TYPE].schema_.ref == "#/components/schemas/User"


def test_openapi_with_embed_body_param():
    app = APIGatewayRestResolver()

    class User(BaseModel):
        name: str

    @app.post("/users")
    def handler(user: Annotated[User, Body(embed=True)]):
        print(user)

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    post = schema.paths["/users"].post
    assert post.parameters is None
    assert post.requestBody is not None

    request_body = post.requestBody
    assert request_body.required is True
    # Notice here we craft a specific schema for the embedded user
    assert request_body.content[JSON_CONTENT_TYPE].schema_.ref == "#/components/schemas/Body_handler_users_post"

    # Ensure that the custom body schema actually points to the real user class
    components = schema.components
    assert "Body_handler_users_post" in components.schemas
    body_post_handler_schema = components.schemas["Body_handler_users_post"]
    assert body_post_handler_schema.properties["user"].ref == "#/components/schemas/User"


def test_openapi_with_body_description():
    app = APIGatewayRestResolver()

    class User(BaseModel):
        name: str

    @app.post("/users")
    def handler(user: Annotated[User, Body(description="This is a user")]):
        print(user)

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    post = schema.paths["/users"].post
    assert post.parameters is None
    assert post.requestBody is not None

    request_body = post.requestBody

    # Description should appear in two places: on the request body and on the schema
    assert request_body.description == "This is a user"
    assert request_body.content[JSON_CONTENT_TYPE].schema_.description == "This is a user"


def test_openapi_with_excluded_operations():
    app = APIGatewayRestResolver()

    @app.get("/secret", include_in_schema=False)
    def secret():
        return "password"

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 0


def test_openapi_with_router_response():
    router = Router()

    @router.put("/example-resource", responses={200: {"description": "Custom response"}})
    def handler():
        pass

    app = APIGatewayRestResolver(enable_validation=True)
    app.include_router(router)

    schema = app.get_openapi_schema()
    put = schema.paths["/example-resource"].put
    assert 200 in put.responses.keys()
    assert put.responses[200].description == "Custom response"


def test_openapi_with_router_tags():
    router = Router()

    @router.put("/example-resource", tags=["Example"])
    def handler():
        pass

    app = APIGatewayRestResolver(enable_validation=True)
    app.include_router(router)

    schema = app.get_openapi_schema()
    tags = schema.paths["/example-resource"].put.tags
    assert len(tags) == 1
    assert tags[0] == "Example"


def test_create_header():
    header = _Header(convert_underscores=True)
    assert header.convert_underscores is True


def test_create_body():
    body = Body(embed=True, examples=[Example(summary="Example 1", value=10)])
    assert body.embed is True


# Tests that when we try to create a model without a field type, we return None
def test_create_empty_model_field():
    result = _create_model_field(None, int, "name", False)
    assert result is None


# Tests that when we try to crate a param model without a source, we default to "query"
def test_create_model_field_with_empty_in():
    field_info = Param()

    result = _create_model_field(field_info, int, "name", False)
    assert result.field_info.in_ == ParamTypes.query


# Tests that when we try to create a model field with convert_underscore, we convert the field name
def test_create_model_field_convert_underscore():
    field_info = _Header(alias=None, convert_underscores=True)

    result = _create_model_field(field_info, int, "user_id", False)
    assert result.alias == "user-id"
