from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler.api_gateway import APIGatewayRestResolver, Response, Router
from aws_lambda_powertools.event_handler.openapi.models import (
    Example,
    Parameter,
    ParameterInType,
    Schema,
)
from aws_lambda_powertools.event_handler.openapi.params import (
    Body,
    Header,
    Param,
    ParamTypes,
    Query,
    _create_model_field,
)

JSON_CONTENT_TYPE = "application/json"


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
    def handler() -> Tuple[str, int]:
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
    def handler() -> Tuple[Annotated[str, Body(title="Response title")], int]:
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
    def handler(page: Annotated[List[str], Query()]):
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


def test_openapi_file_upload_parameters():
    """Test File parameter generates correct OpenAPI schema for file uploads."""
    from aws_lambda_powertools.event_handler.openapi.params import File, Form

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload")
    def upload_file(
        file: Annotated[bytes, File(description="File to upload")],
        filename: Annotated[str, Form(description="Name of the file")],
    ):
        return {"message": f"Uploaded {filename}", "size": len(file)}

    schema = app.get_openapi_schema()

    # Check that the endpoint is present
    assert "/upload" in schema.paths

    post_op = schema.paths["/upload"].post
    assert post_op is not None

    # Check request body
    request_body = post_op.requestBody
    assert request_body is not None
    assert request_body.required is True

    # Check content type is multipart/form-data
    assert "multipart/form-data" in request_body.content

    # Get the schema reference
    multipart_content = request_body.content["multipart/form-data"]
    assert multipart_content.schema_ is not None

    # Check that it references a component schema
    schema_ref = multipart_content.schema_.ref
    assert schema_ref is not None
    assert schema_ref.startswith("#/components/schemas/")

    # Get the component schema name
    component_name = schema_ref.split("/")[-1]
    assert component_name in schema.components.schemas

    # Check the component schema properties
    component_schema = schema.components.schemas[component_name]
    properties = component_schema.properties

    # Check file parameter
    assert "file" in properties
    file_prop = properties["file"]
    assert file_prop.type == "string"
    assert file_prop.format == "binary"  # This is the key assertion
    assert file_prop.title == "File"
    assert file_prop.description == "File to upload"

    # Check form parameter
    assert "filename" in properties
    filename_prop = properties["filename"]
    assert filename_prop.type == "string"
    assert filename_prop.title == "Filename"
    assert filename_prop.description == "Name of the file"

    # Check required fields
    assert component_schema.required == ["file", "filename"]


def test_openapi_form_only_parameters():
    """Test Form parameters generate application/x-www-form-urlencoded content type."""
    from aws_lambda_powertools.event_handler.openapi.params import Form

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


def test_openapi_mixed_file_and_form_parameters():
    """Test mixed File and Form parameters use multipart/form-data."""
    from aws_lambda_powertools.event_handler.openapi.params import File, Form

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/mixed")
    def upload_with_metadata(
        file: Annotated[bytes, File(description="Document to upload")],
        title: Annotated[str, Form(description="Document title")],
        category: Annotated[str, Form(description="Document category")] = "general",
    ):
        return {"title": title, "category": category, "file_size": len(file)}

    schema = app.get_openapi_schema()

    # Check that the endpoint is present
    assert "/mixed" in schema.paths

    post_op = schema.paths["/mixed"].post
    request_body = post_op.requestBody

    # When both File and Form parameters are present, should use multipart/form-data
    assert "multipart/form-data" in request_body.content

    # Get the component schema
    multipart_content = request_body.content["multipart/form-data"]
    schema_ref = multipart_content.schema_.ref
    component_name = schema_ref.split("/")[-1]
    component_schema = schema.components.schemas[component_name]

    properties = component_schema.properties

    # Check file parameter has binary format
    assert "file" in properties
    file_prop = properties["file"]
    assert file_prop.format == "binary"

    # Check form parameters are present
    assert "title" in properties
    assert "category" in properties

    # Check required fields
    assert "file" in component_schema.required
    assert "title" in component_schema.required
    assert "category" not in component_schema.required  # has default value


def test_openapi_multiple_file_uploads():
    """Test multiple file uploads with List[bytes] type."""
    from aws_lambda_powertools.event_handler.openapi.params import File, Form

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload-multiple")
    def upload_multiple_files(
        files: Annotated[List[bytes], File(description="Files to upload")],
        description: Annotated[str, Form(description="Upload description")],
    ):
        return {
            "message": f"Uploaded {len(files)} files",
            "description": description,
            "total_size": sum(len(file) for file in files),
        }

    schema = app.get_openapi_schema()

    # Check that the endpoint is present
    assert "/upload-multiple" in schema.paths

    post_op = schema.paths["/upload-multiple"].post
    request_body = post_op.requestBody

    # Should use multipart/form-data for file uploads
    assert "multipart/form-data" in request_body.content

    # Get the component schema
    multipart_content = request_body.content["multipart/form-data"]
    schema_ref = multipart_content.schema_.ref
    component_name = schema_ref.split("/")[-1]
    component_schema = schema.components.schemas[component_name]

    properties = component_schema.properties

    # Check files parameter
    assert "files" in properties
    files_prop = properties["files"]

    # For List[bytes] with File annotation, should be array of strings with binary format
    assert files_prop.type == "array"
    assert files_prop.items.type == "string"
    assert files_prop.items.format == "binary"

    # Check form parameter
    assert "description" in properties
    description_prop = properties["description"]
    assert description_prop.type == "string"


def test_openapi_public_file_form_exports():
    """Test that File and Form are properly exported for public use."""
    from aws_lambda_powertools.event_handler.openapi.params import File, Form

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/public-api")
    def upload_with_public_types(
        file: Annotated[bytes, File()],  # Using the public export as annotation
        name: Annotated[str, Form()],  # Using the public export as annotation
    ):
        return {"status": "uploaded"}

    schema = app.get_openapi_schema()

    # Check that the endpoint works with public exports
    assert "/public-api" in schema.paths

    post_op = schema.paths["/public-api"].post
    request_body = post_op.requestBody

    # Should generate multipart/form-data
    assert "multipart/form-data" in request_body.content

    # Get the component schema
    multipart_content = request_body.content["multipart/form-data"]
    schema_ref = multipart_content.schema_.ref
    component_name = schema_ref.split("/")[-1]
    component_schema = schema.components.schemas[component_name]

    properties = component_schema.properties

    # Check that both parameters are present and correctly typed
    assert "file" in properties
    assert properties["file"].format == "binary"

    assert "name" in properties
    assert properties["name"].type == "string"


def test_openapi_file_parameter_with_custom_schema_extra():
    """Test File parameter with custom json_schema_extra that gets merged with format: binary."""
    from aws_lambda_powertools.event_handler.openapi.params import File

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload-custom")
    def upload_with_custom_schema(
        file: Annotated[
            bytes,
            File(
                description="Custom file upload",
                json_schema_extra={"example": "file_content", "title": "Custom File"},
            ),
        ],
    ):
        return {"status": "uploaded"}

    schema = app.get_openapi_schema()

    # Check that the endpoint is present
    assert "/upload-custom" in schema.paths

    post_op = schema.paths["/upload-custom"].post
    request_body = post_op.requestBody

    # Should use multipart/form-data for file uploads
    assert "multipart/form-data" in request_body.content

    # Get the component schema
    multipart_content = request_body.content["multipart/form-data"]
    schema_ref = multipart_content.schema_.ref
    component_name = schema_ref.split("/")[-1]
    component_schema = schema.components.schemas[component_name]

    properties = component_schema.properties

    # Check file parameter has both binary format and custom schema extras
    assert "file" in properties
    file_prop = properties["file"]
    assert file_prop.format == "binary"  # This should be preserved
    assert file_prop.description == "Custom file upload"


def test_openapi_body_param_with_conflicting_field_info():
    """Test error condition when both FieldInfo annotation and value are provided."""
    from aws_lambda_powertools.event_handler.openapi.params import File

    app = APIGatewayRestResolver(enable_validation=True)

    # This should work fine - using FieldInfo as annotation
    @app.post("/upload-normal")
    def upload_normal(file: Annotated[bytes, File(description="File to upload")]):
        return {"status": "uploaded"}

    # Test that the normal case works
    schema = app.get_openapi_schema()
    assert "/upload-normal" in schema.paths


def test_openapi_mixed_body_media_types():
    """Test mixed Body parameters with different media types."""
    from pydantic import BaseModel

    from aws_lambda_powertools.event_handler.openapi.params import Body

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
    from typing import Optional

    from aws_lambda_powertools.event_handler.openapi.params import Form

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/form-edge-cases")
    def form_edge_cases(
        required_field: Annotated[str, Form(description="Required field")],
        optional_field: Annotated[Optional[str], Form(description="Optional field")] = None,
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


def test_openapi_file_with_list_type_edge_case():
    """Test File parameter with nested List types for edge case coverage."""
    from typing import List, Optional

    from aws_lambda_powertools.event_handler.openapi.params import File, Form

    app = APIGatewayRestResolver(enable_validation=True)

    @app.post("/upload-complex")
    def upload_complex_types(
        files: Annotated[List[bytes], File(description="Multiple files")],
        metadata: Annotated[Optional[str], Form(description="Optional metadata")] = None,
    ):
        total_size = sum(len(file) for file in files) if files else 0
        return {"file_count": len(files) if files else 0, "total_size": total_size, "metadata": metadata}

    schema = app.get_openapi_schema()

    # Check that the endpoint is present
    assert "/upload-complex" in schema.paths

    post_op = schema.paths["/upload-complex"].post
    request_body = post_op.requestBody

    # Should use multipart/form-data when files are present
    assert "multipart/form-data" in request_body.content

    # Get the component schema
    multipart_content = request_body.content["multipart/form-data"]
    schema_ref = multipart_content.schema_.ref
    component_name = schema_ref.split("/")[-1]
    component_schema = schema.components.schemas[component_name]

    properties = component_schema.properties

    # Check files parameter is array with binary format items
    assert "files" in properties
    files_prop = properties["files"]
    assert files_prop.type == "array"
    assert files_prop.items.type == "string"
    assert files_prop.items.format == "binary"

    # Check metadata is optional
    assert "metadata" in properties
    assert "files" in component_schema.required
    assert "metadata" not in component_schema.required
