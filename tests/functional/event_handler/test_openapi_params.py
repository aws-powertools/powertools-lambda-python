from dataclasses import dataclass

from pydantic import BaseModel

from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
from aws_lambda_powertools.event_handler.openapi.models import (
    Parameter,
    ParameterInType,
    Schema,
)


def test_openapi_no_params():
    app = ApiGatewayResolver()

    @app.get("/")
    def handler():
        pass

    schema = app.get_openapi_schema(title="Hello API", version="1.0.0")

    assert len(schema.paths.keys()) == 1
    assert "/" in schema.paths

    path = schema.paths["/"]
    assert path.get

    get = path.get
    assert get.summary == "GET /"
    assert get.operationId == "GetHandler"

    assert "200" in get.responses
    response = get.responses["200"]
    assert response.description == "Success"

    assert "application/json" in response.content
    json_response = response.content["application/json"]
    assert json_response.schema_ == Schema()
    assert not json_response.examples
    assert not json_response.encoding


def test_openapi_with_scalar_params():
    app = ApiGatewayResolver()

    @app.get("/users/<user_id>")
    def handler(user_id: str, include_extra: bool = False):
        pass

    schema = app.get_openapi_schema(title="Hello API", version="1.0.0")

    assert len(schema.paths.keys()) == 1
    assert "/users/<user_id>" in schema.paths

    path = schema.paths["/users/<user_id>"]
    assert path.get

    get = path.get
    assert get.summary == "GET /users/<user_id>"
    assert get.operationId == "GetHandler"
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


def test_openapi_with_scalar_returns():
    app = ApiGatewayResolver()

    @app.get("/")
    def handler() -> str:
        return "Hello, world"

    schema = app.get_openapi_schema(title="Hello API", version="1.0.0")
    assert len(schema.paths.keys()) == 1

    get = schema.paths["/"].get
    assert get.parameters is None

    response = get.responses["200"].content["application/json"]
    assert response.schema_.title == "Return"
    assert response.schema_.type == "string"


def test_openapi_with_pydantic_returns():
    app = ApiGatewayResolver()

    class User(BaseModel):
        name: str

    @app.get("/")
    def handler() -> User:
        return User(name="Ruben Fonseca")

    schema = app.get_openapi_schema(title="Hello API", version="1.0.0")
    assert len(schema.paths.keys()) == 1

    get = schema.paths["/"].get
    assert get.parameters is None

    response = get.responses["200"].content["application/json"]
    reference = response.schema_
    assert reference.ref == "#/components/schemas/User"

    assert "User" in schema.components.schemas
    user_schema = schema.components.schemas["User"]
    assert isinstance(user_schema, Schema)
    assert user_schema.title == "User"
    assert "name" in user_schema.properties


def test_openapi_with_dataclasse_return():
    app = ApiGatewayResolver()

    @dataclass
    class User:
        surname: str

    @app.get("/")
    def handler() -> User:
        return User(name="Ruben Fonseca")

    schema = app.get_openapi_schema(title="Hello API", version="1.0.0")
    assert len(schema.paths.keys()) == 1

    get = schema.paths["/"].get
    assert get.parameters is None

    response = get.responses["200"].content["application/json"]
    reference = response.schema_
    assert reference.ref == "#/components/schemas/User"

    assert "User" in schema.components.schemas
    user_schema = schema.components.schemas["User"]
    assert isinstance(user_schema, Schema)
    assert user_schema.title == "User"
    assert "surname" in user_schema.properties
