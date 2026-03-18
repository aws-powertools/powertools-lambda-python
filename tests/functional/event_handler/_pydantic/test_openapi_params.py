import json
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

import pytest
from pydantic import BaseModel, Field

from aws_lambda_powertools.event_handler.api_gateway import APIGatewayRestResolver, Response, Router
from aws_lambda_powertools.event_handler.openapi.models import (
    Example,
    Parameter,
    ParameterInType,
    Schema,
)
from aws_lambda_powertools.event_handler.openapi.params import (
    Body,
    Form,
    Header,
    Param,
    ParamTypes,
    Query,
    _create_model_field,
)

JSON_CONTENT_TYPE = "application/json"


def test_openapi_pydantic_query_params():
    """Test that Pydantic models in Query parameters are expanded into individual fields in OpenAPI schema"""
    app = APIGatewayRestResolver()

    class QueryParams(BaseModel):
        limit: int = Field(default=10, ge=1, le=100, description="Number of items to return")
        offset: int = Field(default=0, ge=0, description="Number of items to skip")
        search: str | None = Field(default=None, description="Search term")

    @app.get("/search")
    def search_handler(params: Annotated[QueryParams, Query()]):
        return {"message": "success"}

    schema = app.get_openapi_schema()

    # Check that the path exists
    assert "/search" in schema.paths
    path = schema.paths["/search"]
    assert path.get is not None

    # Check that parameters are expanded
    get_operation = path.get
    assert get_operation.parameters is not None
    assert len(get_operation.parameters) == 3

    # Check individual parameters
    param_names = [param.name for param in get_operation.parameters]
    assert "limit" in param_names
    assert "offset" in param_names
    assert "search" in param_names

    # Check parameter details
    for param in get_operation.parameters:
        assert param.in_ == ParameterInType.query
        if param.name == "limit":
            assert param.required is False  # Has default value
            assert param.description == "Number of items to return"
            assert param.schema_.type == "integer"
        elif param.name == "offset":
            assert param.required is False  # Has default value
            assert param.description == "Number of items to skip"
            assert param.schema_.type == "integer"
        elif param.name == "search":
            assert param.required is False  # Optional field
            assert param.description == "Search term"
            assert param.schema_.type == "string"


def test_openapi_pydantic_header_params():
    """Test that Pydantic models in Header parameters are expanded into individual fields in OpenAPI schema"""
    app = APIGatewayRestResolver()

    class HeaderParams(BaseModel):
        authorization: str = Field(description="Authorization token")
        user_agent: str = Field(default="PowerTools/1.0", description="User agent")
        language: str | None = Field(default=None, alias="accept-language", description="Language preference")

    @app.get("/protected")
    def protected_handler(headers: Annotated[HeaderParams, Header()]):
        return {"message": "success"}

    schema = app.get_openapi_schema()

    # Check that the path exists
    assert "/protected" in schema.paths
    path = schema.paths["/protected"]
    assert path.get is not None

    # Check that parameters are expanded
    get_operation = path.get
    assert get_operation.parameters is not None
    assert len(get_operation.parameters) == 3

    # Check individual parameters
    param_names = [param.name for param in get_operation.parameters]
    assert "authorization" in param_names
    assert "user-agent" in param_names  # headers are always spinal-case
    assert "accept-language" in param_names  # Should use alias

    # Check parameter details
    for param in get_operation.parameters:
        assert param.in_ == ParameterInType.header
        if param.name == "authorization":
            assert param.required is True  # No default value
            assert param.description == "Authorization token"
            assert param.schema_.type == "string"
        elif param.name == "user_agent":
            assert param.required is False  # Has default value
            assert param.description == "User agent"
            assert param.schema_.type == "string"
        elif param.name == "accept-language":
            assert param.required is False  # Optional field
            assert param.description == "Language preference"
            assert param.schema_.type == "string"


def test_openapi_pydantic_mixed_params():
    """Test that mixed Pydantic models (Query + Header) work together"""
    app = APIGatewayRestResolver()

    class QueryParams(BaseModel):
        q: str = Field(description="Search query")
        limit: int = Field(default=10, description="Number of results")

    class HeaderParams(BaseModel):
        authorization: str = Field(description="Bearer token")

    @app.get("/mixed")
    def mixed_handler(query: Annotated[QueryParams, Query()], headers: Annotated[HeaderParams, Header()]):
        return {"message": "success"}

    schema = app.get_openapi_schema()

    # Check that the path exists
    assert "/mixed" in schema.paths
    path = schema.paths["/mixed"]
    assert path.get is not None

    # Check that all parameters are expanded
    get_operation = path.get
    assert get_operation.parameters is not None
    assert len(get_operation.parameters) == 3  # 2 query + 1 header

    # Check parameter types
    query_params = [p for p in get_operation.parameters if p.in_ == ParameterInType.query]
    header_params = [p for p in get_operation.parameters if p.in_ == ParameterInType.header]

    assert len(query_params) == 2
    assert len(header_params) == 1

    # Check specific parameters
    query_names = [p.name for p in query_params]
    assert "q" in query_names
    assert "limit" in query_names

    header_names = [p.name for p in header_params]
    assert "authorization" in header_names


def test_openapi_no_params():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler():
        raise NotImplementedError()

    schema = app.get_openapi_schema()
    assert schema.info.title == "Powertools for AWS Lambda (Python) API"
    assert schema.info.version == "1.0.0"

    assert len(schema.paths.keys()) == 1
    assert "/" in schema.paths

    path = schema.paths["/"]
    assert path.get

    get = path.get
    assert get.summary == "GET /"
    assert get.operationId == "handler__get"
    assert get.deprecated is None

    assert get.responses is not None
    assert 200 in get.responses.keys()
    response = get.responses[200]
    assert response.description == "Successful Response"

    assert JSON_CONTENT_TYPE in response.content
    json_response = response.content[JSON_CONTENT_TYPE]
    assert json_response.schema_ is None
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
    example = Example(**parameter.schema_.examples[0])
    assert example.summary == "Example 1"
    assert example.value == 10


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


def test_openapi_with_tuple_returns():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler() -> tuple[str, int]:
        return "Hello, world", 200

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    get = schema.paths["/"].get
    assert get.parameters is None

    response = get.responses[200].content[JSON_CONTENT_TYPE]
    assert response.schema_.title == "Return"
    assert response.schema_.type == "string"


def test_openapi_with_tuple_annotated_returns():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler() -> tuple[Annotated[str, Body(title="Response title")], int]:
        return "Hello, world", 200

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


def test_openapi_with_list_param():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handler(page: Annotated[list[str], Query()]):
        return page

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    get = schema.paths["/"].get
    assert get.parameters[0].schema_.type == "array"


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
        return User(name="Powertools")

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
        orders: list[Order]

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


def test_openapi_with_body_examples():
    app = APIGatewayRestResolver()

    first_example = Example(summary="Example1", description="Example1", value={"name": "Alice"})
    second_example = Example(summary="Example2", description="Example2", value={"name": "Bob"})

    class User(BaseModel):
        name: str

    @app.post("/users")
    def handler(
        user: Annotated[
            User,
            Body(
                openapi_examples={
                    "example1": first_example,
                    "example2": second_example,
                },
            ),
        ],
    ):
        print(user)

    schema = app.get_openapi_schema()
    assert len(schema.paths.keys()) == 1

    post = schema.paths["/users"].post
    assert post.parameters is None
    assert post.requestBody is not None

    request_body = post.requestBody

    # Examples should appear in the request_body content schema
    request_body_examples = request_body.content[JSON_CONTENT_TYPE].examples

    assert request_body_examples["example1"] == first_example
    assert request_body_examples["example2"] == second_example


def test_openapi_with_deprecated_operations():
    app = APIGatewayRestResolver()

    @app.get("/", deprecated=True)
    def _get():
        raise NotImplementedError()

    @app.post("/", deprecated=True)
    def _post():
        raise NotImplementedError()

    schema = app.get_openapi_schema()

    get = schema.paths["/"].get
    assert get.deprecated is True

    post = schema.paths["/"].post
    assert post.deprecated is True


def test_openapi_without_deprecated_operations():
    app = APIGatewayRestResolver()

    @app.get("/")
    def _get():
        raise NotImplementedError()

    @app.post("/", deprecated=False)
    def _post():
        raise NotImplementedError()

    schema = app.get_openapi_schema()

    get = schema.paths["/"].get
    assert get.deprecated is None

    post = schema.paths["/"].post
    assert post.deprecated is None


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
    header = Header(convert_underscores=True)
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
    field_info = Header(alias=None, convert_underscores=True)

    result = _create_model_field(field_info, int, "user_id", False)
    assert result.alias == "user-id"


def test_openapi_with_example_as_list():
    app = APIGatewayRestResolver()

    @app.get("/users", summary="Get Users", operation_id="GetUsers", description="Get paginated users", tags=["Users"])
    def handler(
        count: Annotated[
            int,
            Query(gt=0, lt=100, examples=["Example 1"]),
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
    assert parameter.schema_.examples[0] == "Example 1"


def test_openapi_with_examples_of_base_model_field():
    app = APIGatewayRestResolver()

    class Todo(BaseModel):
        id: int = Field(examples=[1])
        title: str = Field(examples=["Example 1"])
        priority: float = Field(examples=[0.5])
        completed: bool = Field(examples=[True])

    @app.get("/")
    def handler() -> Todo:
        return Todo(id=0, title="", priority=0.0, completed=False)

    schema = app.get_openapi_schema()
    assert "Todo" in schema.components.schemas
    todo_schema = schema.components.schemas["Todo"]
    assert isinstance(todo_schema, Schema)

    assert "id" in todo_schema.properties
    id_property = todo_schema.properties["id"]
    assert id_property.examples == [1]

    assert "title" in todo_schema.properties
    title_property = todo_schema.properties["title"]
    assert title_property.examples == ["Example 1"]

    assert "priority" in todo_schema.properties
    priority_property = todo_schema.properties["priority"]
    assert priority_property.examples == [0.5]

    assert "completed" in todo_schema.properties
    completed_property = todo_schema.properties["completed"]
    assert completed_property.examples == [True]


def test_openapi_with_openapi_example():
    app = APIGatewayRestResolver()

    first_example = Example(summary="Example1", description="Example1", value="a")
    second_example = Example(summary="Example2", description="Example2", value="b")

    @app.get("/users", summary="Get Users", operation_id="GetUsers", description="Get paginated users", tags=["Users"])
    def handler(
        count: Annotated[
            int,
            Query(
                openapi_examples={
                    "first_example": first_example,
                    "second_example": second_example,
                },
            ),
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
    assert parameter.examples["first_example"] == first_example
    assert parameter.examples["second_example"] == second_example
    assert parameter.in_ == ParameterInType.query
    assert parameter.schema_.type == "integer"
    assert parameter.schema_.default == 1
    assert parameter.schema_.title == "Count"


def test_openapi_form_only_parameters():
    """Test Form parameters generate application/x-www-form-urlencoded content type."""
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/form-data")
    def create_form_data(
        name: Annotated[str, Form(description="User name")],
        email: Annotated[str, Form(description="User email")] = "test@example.com",
    ):
        return {"name": name, "email": email}

    schema = app.get_openapi_schema()

    # Check that the endpoint is present
    assert "/form-data" in schema.paths

    post_op = schema.paths["/form-data"].post
    assert post_op is not None

    # Check request body
    request_body = post_op.requestBody
    assert request_body is not None

    # Check content type is application/x-www-form-urlencoded
    assert "application/x-www-form-urlencoded" in request_body.content

    # Get the schema reference
    form_content = request_body.content["application/x-www-form-urlencoded"]
    assert form_content.schema_ is not None

    # Check that it references a component schema
    schema_ref = form_content.schema_.ref
    assert schema_ref is not None
    assert schema_ref.startswith("#/components/schemas/")

    # Get the component schema
    component_name = schema_ref.split("/")[-1]
    assert component_name in schema.components.schemas

    component_schema = schema.components.schemas[component_name]
    properties = component_schema.properties

    # Check form parameters
    assert "name" in properties
    name_prop = properties["name"]
    assert name_prop.type == "string"
    assert name_prop.description == "User name"

    assert "email" in properties
    email_prop = properties["email"]
    assert email_prop.type == "string"
    assert email_prop.description == "User email"
    assert email_prop.default == "test@example.com"

    # Check required fields (only name should be required since email has default)
    assert component_schema.required == ["name"]


def test_openapi_mixed_body_media_types():
    """Test mixed Body parameters with different media types."""

    class UserData(BaseModel):
        name: str
        email: str

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/mixed-body")
    def mixed_body_endpoint(user_data: Annotated[UserData, Body(media_type="application/json")]):
        return {"status": "created"}

    schema = app.get_openapi_schema()

    # Check that the endpoint uses the specified media type
    assert "/mixed-body" in schema.paths

    post_op = schema.paths["/mixed-body"].post
    request_body = post_op.requestBody

    # Should use the specified media type
    assert "application/json" in request_body.content


def test_openapi_form_parameter_edge_cases():
    """Test Form parameters with various edge cases."""

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/form-edge-cases")
    def form_edge_cases(
        required_field: Annotated[str, Form(description="Required field")],
        optional_field: Annotated[str | None, Form(description="Optional field")] = None,
        field_with_default: Annotated[str, Form(description="Field with default")] = "default_value",
    ):
        return {"required": required_field, "optional": optional_field, "default": field_with_default}

    schema = app.get_openapi_schema()

    # Check that the endpoint is present
    assert "/form-edge-cases" in schema.paths

    post_op = schema.paths["/form-edge-cases"].post
    request_body = post_op.requestBody

    # Should use application/x-www-form-urlencoded for form-only parameters
    assert "application/x-www-form-urlencoded" in request_body.content

    # Get the component schema
    form_content = request_body.content["application/x-www-form-urlencoded"]
    schema_ref = form_content.schema_.ref
    component_name = schema_ref.split("/")[-1]
    component_schema = schema.components.schemas[component_name]

    properties = component_schema.properties

    # Check all fields are present
    assert "required_field" in properties
    assert "optional_field" in properties
    assert "field_with_default" in properties

    # Check required vs optional handling
    assert "required_field" in component_schema.required
    assert "optional_field" not in component_schema.required  # Optional
    assert "field_with_default" not in component_schema.required  # Has default


def test_openapi_pydantic_query_with_constraints():
    """Test that Pydantic field constraints are preserved in OpenAPI schema"""
    app = APIGatewayRestResolver()

    class QueryParams(BaseModel):
        limit: int = Field(ge=1, le=100, description="Number of items")
        name: str = Field(min_length=1, max_length=50, description="Name filter")

    @app.get("/items")
    def get_items(params: Annotated[QueryParams, Query()]):
        return {"message": "success"}

    schema = app.get_openapi_schema()
    path = schema.paths["/items"]
    get_operation = path.get

    # Find the limit parameter
    limit_param = next(p for p in get_operation.parameters if p.name == "limit")
    assert limit_param.schema_.type == "integer"
    assert limit_param.description == "Number of items"

    # Find the name parameter
    name_param = next(p for p in get_operation.parameters if p.name == "name")
    assert name_param.schema_.type == "string"
    assert name_param.description == "Name filter"


def test_openapi_pydantic_header_with_alias():
    """Test that Pydantic field aliases work correctly in Header parameters"""
    app = APIGatewayRestResolver()

    class HeaderParams(BaseModel):
        content_type: str = Field(alias="content-type", description="Content type")
        user_agent: str = Field(alias="user-agent", description="User agent")

    @app.get("/test")
    def test_handler(headers: Annotated[HeaderParams, Header()]):
        return {"message": "success"}

    schema = app.get_openapi_schema()
    path = schema.paths["/test"]
    get_operation = path.get

    # Check that aliases are used as parameter names
    param_names = [param.name for param in get_operation.parameters]
    assert "content-type" in param_names
    assert "user-agent" in param_names
    assert "content_type" not in param_names  # Original field name should not be used
    assert "user_agent" not in param_names


def test_openapi_pydantic_required_vs_optional():
    """Test that required vs optional fields are correctly identified"""
    app = APIGatewayRestResolver()

    class QueryParams(BaseModel):
        required_field: str = Field(description="Required field")
        optional_with_default: str = Field(default="default", description="Optional with default")
        optional_nullable: str | None = Field(default=None, description="Optional nullable")

    @app.get("/test")
    def test_handler(params: Annotated[QueryParams, Query()]):
        return {"message": "success"}

    schema = app.get_openapi_schema()
    path = schema.paths["/test"]
    get_operation = path.get

    for param in get_operation.parameters:
        if param.name == "required_field":
            assert param.required is True
        elif param.name == "optional_with_default":
            assert param.required is False
        elif param.name == "optional_nullable":
            assert param.required is False


def test_openapi_pydantic_backward_compatibility():
    """Test that existing Body parameter behavior is unchanged"""
    app = APIGatewayRestResolver()

    class BodyModel(BaseModel):
        name: str = Field(description="Name")
        age: int = Field(description="Age")

    @app.post("/users")
    def create_user(user: BodyModel):  # No annotation - should work as Body
        return {"message": "success"}

    schema = app.get_openapi_schema()
    path = schema.paths["/users"]
    post_operation = path.post

    # Should have no parameters (body is handled separately)
    assert post_operation.parameters is None or len(post_operation.parameters) == 0

    # Should have request body
    assert post_operation.requestBody is not None
    assert "application/json" in post_operation.requestBody.content


def test_openapi_pydantic_complex_types():
    """Test that complex types are handled correctly"""
    app = APIGatewayRestResolver()

    class QueryParams(BaseModel):
        string_field: str = Field(description="String field")
        int_field: int = Field(description="Integer field")
        float_field: float = Field(description="Float field")
        bool_field: bool = Field(description="Boolean field")

    @app.get("/complex")
    def complex_handler(params: Annotated[QueryParams, Query()]):
        return {"message": "success"}

    schema = app.get_openapi_schema()
    path = schema.paths["/complex"]
    get_operation = path.get

    type_mapping = {}
    for param in get_operation.parameters:
        type_mapping[param.name] = param.schema_.type

    assert type_mapping["string_field"] == "string"
    assert type_mapping["int_field"] == "integer"
    assert type_mapping["float_field"] == "number"
    assert type_mapping["bool_field"] == "boolean"


@pytest.mark.parametrize(
    "body_value,expected_value",
    [
        ("50", 50),  # Valid: within range
        ("0", 0),  # Valid: at lower bound
        ("100", 100),  # Valid: at upper bound
    ],
)
def test_annotated_types_interval_constraints_in_body_params(body_value, expected_value):
    """
    Test for issue #7600: Validate that annotated_types.Interval constraints
    are properly enforced in Body parameters with valid values.
    """
    from annotated_types import Interval

    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # AND a constrained type using annotated_types.Interval
    ConstrainedInt = Annotated[int, Interval(ge=0, le=100)]

    @app.post("/items")
    def create_item(value: Annotated[ConstrainedInt, Body()]):
        return {"value": value}

    # WHEN sending a request with a valid value
    event = {
        "resource": "/items",
        "path": "/items",
        "httpMethod": "POST",
        "body": body_value,
        "isBase64Encoded": False,
    }

    # THEN the request should succeed
    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["value"] == expected_value


@pytest.mark.parametrize(
    "body_value",
    [
        "-1",  # Invalid: below range
        "101",  # Invalid: above range
    ],
)
def test_annotated_types_interval_constraints_in_body_params_invalid(body_value):
    """
    Test for issue #7600: Validate that annotated_types.Interval constraints
    reject invalid values in Body parameters.
    """
    from annotated_types import Interval

    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # AND a constrained type using annotated_types.Interval
    constrained_int = Annotated[int, Interval(ge=0, le=100)]

    @app.post("/items")
    def create_item(value: Annotated[constrained_int, Body()]):
        return {"value": value}

    # WHEN sending a request with an invalid value
    event = {
        "resource": "/items",
        "path": "/items",
        "httpMethod": "POST",
        "body": body_value,
        "isBase64Encoded": False,
    }

    # THEN validation should fail
    result = app(event, {})
    assert result["statusCode"] == 422


@pytest.mark.parametrize(
    "query_value,expected_value",
    [
        ("50", 50),  # Valid: within range
        ("0", 0),  # Valid: at lower bound
        ("100", 100),  # Valid: at upper bound
    ],
)
def test_annotated_types_interval_constraints_in_query_params(query_value, expected_value):
    """
    Test for issue #7600: Validate that annotated_types.Interval constraints
    are properly enforced in Query parameters with valid values.
    """
    from annotated_types import Interval

    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # AND a constrained type using annotated_types.Interval
    constrained_int = Annotated[int, Interval(ge=0, le=100)]

    @app.get("/items")
    def list_items(limit: Annotated[constrained_int, Query()]):
        return {"limit": limit}

    # WHEN sending a request with a valid value
    event = {
        "resource": "/items",
        "path": "/items",
        "httpMethod": "GET",
        "queryStringParameters": {"limit": query_value},
        "isBase64Encoded": False,
    }

    # THEN the request should succeed
    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["limit"] == expected_value


@pytest.mark.parametrize(
    "query_value",
    [
        "-1",  # Invalid: below range
        "101",  # Invalid: above range
    ],
)
def test_annotated_types_interval_constraints_in_query_params_invalid(query_value):
    """
    Test for issue #7600: Validate that annotated_types.Interval constraints
    reject invalid values in Query parameters.
    """
    from annotated_types import Interval

    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # AND a constrained type using annotated_types.Interval
    constrained_int = Annotated[int, Interval(ge=0, le=100)]

    @app.get("/items")
    def list_items(limit: Annotated[constrained_int, Query()]):
        return {"limit": limit}

    # WHEN sending a request with an invalid value
    event = {
        "resource": "/items",
        "path": "/items",
        "httpMethod": "GET",
        "queryStringParameters": {"limit": query_value},
        "isBase64Encoded": False,
    }

    # THEN validation should fail
    result = app(event, {})
    assert result["statusCode"] == 422


def test_annotated_types_interval_in_openapi_schema():
    """
    Test that annotated_types.Interval constraints are reflected in the OpenAPI schema.
    """
    from annotated_types import Interval

    app = APIGatewayRestResolver()
    constrained_int = Annotated[int, Interval(ge=0, le=100)]

    @app.get("/items")
    def list_items(limit: Annotated[constrained_int, Query()] = 10):
        return {"limit": limit}

    schema = app.get_openapi_schema()

    # Verify the Query parameter schema includes constraints
    get_operation = schema.paths["/items"].get
    limit_param = next(p for p in get_operation.parameters if p.name == "limit")

    assert limit_param.schema_.type == "integer"
    assert limit_param.schema_.default == 10
    assert limit_param.required is False


def test_query_alias_sets_validation_alias_automatically():
    """
    When alias is set but validation_alias is not,
    validation_alias should be automatically set to alias value.
    This ensures compatibility with Pydantic 2.12+.
    """
    from annotated_types import Ge, Le
    from pydantic import StringConstraints

    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # AND constrained types using annotated_types
    IntQuery = Annotated[int, Ge(1), Le(100)]
    StrQuery = Annotated[str, StringConstraints(min_length=4, max_length=128)]

    @app.get("/foo")
    def get_foo(
        str_query: Annotated[StrQuery, Query(alias="strQuery")],
        int_query: Annotated[IntQuery, Query(alias="intQuery")],
    ):
        return {"int_query": int_query, "str_query": str_query}

    # WHEN sending a request with aliased query parameters
    event = {
        "httpMethod": "GET",
        "path": "/foo",
        "queryStringParameters": {
            "intQuery": "20",
            "strQuery": "fooBarFizzBuzz",
        },
    }

    # THEN the request should succeed with correct values
    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["int_query"] == 20
    assert body["str_query"] == "fooBarFizzBuzz"


def test_query_alias_with_multivalue_query_string_parameters():
    """
    Ensure alias works with multiValueQueryStringParameters.
    """
    from annotated_types import Ge, Le
    from pydantic import StringConstraints

    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    IntQuery = Annotated[int, Ge(1), Le(100)]
    StrQuery = Annotated[str, StringConstraints(min_length=4, max_length=128)]

    @app.get("/foo")
    def get_foo(
        str_query: Annotated[StrQuery, Query(alias="strQuery")],
        int_query: Annotated[IntQuery, Query(alias="intQuery")],
    ):
        return {"int_query": int_query, "str_query": str_query}

    # WHEN sending a request with multiValueQueryStringParameters
    event = {
        "httpMethod": "GET",
        "path": "/foo",
        "multiValueQueryStringParameters": {
            "intQuery": ["20"],
            "strQuery": ["fooBarFizzBuzz"],
        },
    }

    # THEN the request should succeed
    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["int_query"] == 20
    assert body["str_query"] == "fooBarFizzBuzz"


def test_query_explicit_validation_alias_takes_precedence():
    """
    Explicitly set validation_alias is preserved and not overwritten by alias.
    The alias is used by Powertools to extract the value from the request,
    while validation_alias is used by Pydantic for internal validation.
    """
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/foo")
    def get_foo(
        my_param: Annotated[str, Query(alias="aliasName", validation_alias="validationAliasName")],
    ):
        return {"my_param": my_param}

    # WHEN sending a request with the alias name (used by Powertools to extract value)
    event = {
        "httpMethod": "GET",
        "path": "/foo",
        "queryStringParameters": {
            "aliasName": "test_value",
        },
    }

    # THEN the request should succeed using alias for extraction
    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["my_param"] == "test_value"


def test_header_alias_sets_validation_alias_automatically():
    """
    Header alias should also set validation_alias automatically.
    """
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/foo")
    def get_foo(
        custom_header: Annotated[str, Header(alias="X-Custom-Header")],
    ):
        return {"custom_header": custom_header}

    # WHEN sending a request with the aliased header
    event = {
        "httpMethod": "GET",
        "path": "/foo",
        "headers": {
            "X-Custom-Header": "header_value",
        },
    }

    # THEN the request should succeed
    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["custom_header"] == "header_value"


def test_query_without_alias_works_normally():
    """
    Query without alias continues to work normally.
    """
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/foo")
    def get_foo(
        my_param: Annotated[str, Query()],
    ):
        return {"my_param": my_param}

    # WHEN sending a request with the parameter name
    event = {
        "httpMethod": "GET",
        "path": "/foo",
        "queryStringParameters": {
            "my_param": "test_value",
        },
    }

    # THEN the request should succeed
    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["my_param"] == "test_value"


def test_query_validation_alias_only_sets_alias_automatically():
    """
    When only validation_alias is set (without alias),
    alias should be automatically set to validation_alias value.
    This ensures the middleware can find the parameter in the request.
    """
    from annotated_types import Ge, Le
    from pydantic import StringConstraints

    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    IntQuery = Annotated[int, Ge(1), Le(100)]
    StrQuery = Annotated[str, StringConstraints(min_length=4, max_length=128)]

    @app.get("/foo")
    def get_foo(
        str_query: Annotated[StrQuery, Query(validation_alias="strQuery")],
        int_query: Annotated[IntQuery, Query(validation_alias="intQuery")],
    ):
        return {"int_query": int_query, "str_query": str_query}

    # WHEN sending a request with validation_alias names
    event = {
        "httpMethod": "GET",
        "path": "/foo",
        "queryStringParameters": {
            "intQuery": "20",
            "strQuery": "fooBarFizzBuzz",
        },
    }

    # THEN the request should succeed
    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["int_query"] == 20
    assert body["str_query"] == "fooBarFizzBuzz"


def test_body_alias_sets_validation_alias_automatically():
    """
    When alias is set but validation_alias is not in Body,
    validation_alias should be automatically set to alias value.
    """
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/foo")
    def post_foo(
        my_body: Annotated[str, Body(alias="myBody")],
    ):
        return {"my_body": my_body}

    # WHEN sending a request with body
    event = {
        "httpMethod": "POST",
        "path": "/foo",
        "body": '"test_value"',
    }

    # THEN the request should succeed
    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["my_body"] == "test_value"


def test_body_validation_alias_only_sets_alias_automatically():
    """
    When only validation_alias is set (without alias) in Body,
    alias should be automatically set to validation_alias value.
    """
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/foo")
    def post_foo(
        my_body: Annotated[str, Body(validation_alias="myBody")],
    ):
        return {"my_body": my_body}

    # WHEN sending a request with body
    event = {
        "httpMethod": "POST",
        "path": "/foo",
        "body": '"test_value"',
    }

    # THEN the request should succeed
    result = app(event, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["my_body"] == "test_value"


def test_body_class_annotation_without_parentheses():
    """
    GIVEN an endpoint using Body class (not instance) in Annotated
    WHEN sending a valid request body
    THEN the request should be validated correctly
    """
    app = APIGatewayRestResolver(enable_validation=True)

    class MyRequest(BaseModel):
        foo: str
        bar: str = "default_bar"

    class MyResponse(BaseModel):
        concatenated: str

    # Using Body (class) instead of Body() (instance)
    @app.patch("/test")
    def handler(body: Annotated[MyRequest, Body]) -> MyResponse:
        return MyResponse(concatenated=body.foo + body.bar)

    event = {
        "resource": "/test",
        "path": "/test",
        "httpMethod": "PATCH",
        "body": '{"foo": "hello"}',
        "isBase64Encoded": False,
    }

    result = app(event, {})
    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["concatenated"] == "hellodefault_bar"


def test_body_instance_annotation_with_parentheses():
    """
    GIVEN an endpoint using Body() instance in Annotated
    WHEN sending a valid request body
    THEN the request should be validated correctly
    """
    app = APIGatewayRestResolver(enable_validation=True)

    class MyRequest(BaseModel):
        foo: str
        bar: str = "default_bar"

    class MyResponse(BaseModel):
        concatenated: str

    # Using Body() (instance)
    @app.patch("/test")
    def handler(body: Annotated[MyRequest, Body()]) -> MyResponse:
        return MyResponse(concatenated=body.foo + body.bar)

    event = {
        "resource": "/test",
        "path": "/test",
        "httpMethod": "PATCH",
        "body": '{"foo": "hello"}',
        "isBase64Encoded": False,
    }

    result = app(event, {})
    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["concatenated"] == "hellodefault_bar"


def test_query_class_annotation_without_parentheses():
    """
    GIVEN an endpoint using Query class (not instance) in Annotated
    WHEN sending a valid query parameter
    THEN the request should be validated correctly
    """
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/test")
    def handler(name: Annotated[str, Query]) -> dict:
        return {"name": name}

    event = {
        "resource": "/test",
        "path": "/test",
        "httpMethod": "GET",
        "queryStringParameters": {"name": "hello"},
        "isBase64Encoded": False,
    }

    result = app(event, {})
    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["name"] == "hello"


def test_header_class_annotation_without_parentheses():
    """
    GIVEN an endpoint using Header class (not instance) in Annotated
    WHEN sending a valid header
    THEN the request should be validated correctly
    """
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/test")
    def handler(x_custom: Annotated[str, Header]) -> dict:
        return {"header": x_custom}

    event = {
        "resource": "/test",
        "path": "/test",
        "httpMethod": "GET",
        "headers": {"x-custom": "my-value"},
        "isBase64Encoded": False,
    }

    result = app(event, {})
    assert result["statusCode"] == 200
    response_body = json.loads(result["body"])
    assert response_body["header"] == "my-value"
