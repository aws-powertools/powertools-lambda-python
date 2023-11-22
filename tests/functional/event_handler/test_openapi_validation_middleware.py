import json
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePath
from typing import List, Tuple

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.openapi.params import Body
from aws_lambda_powertools.shared.types import Annotated
from tests.functional.utils import load_event

LOAD_GW_EVENT = load_event("apiGatewayProxyEvent.json")


def test_validate_scalars():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a scalar parameter
    @app.get("/users/<user_id>")
    def handler(user_id: int):
        print(user_id)

    # sending a number
    LOAD_GW_EVENT["path"] = "/users/123"

    # THEN the handler should be invoked and return 200
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200

    # sending a string
    LOAD_GW_EVENT["path"] = "/users/abc"

    # THEN the handler should be invoked and return 422
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer", "int_parsing"])


def test_validate_scalars_with_default():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter
    @app.get("/users/<user_id>")
    def handler(user_id: int = 123):
        print(user_id)

    # sending a number
    LOAD_GW_EVENT["path"] = "/users/123"

    # THEN the handler should be invoked and return 200
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200

    # sending a string
    LOAD_GW_EVENT["path"] = "/users/abc"

    # THEN the handler should be invoked and return 422
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer", "int_parsing"])


def test_validate_scalars_with_default_and_optional():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter
    @app.get("/users/<user_id>")
    def handler(user_id: int = 123, include_extra: bool = False):
        print(user_id)

    # sending a number
    LOAD_GW_EVENT["path"] = "/users/123"

    # THEN the handler should be invoked and return 200
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200

    # sending a string
    LOAD_GW_EVENT["path"] = "/users/abc"

    # THEN the handler should be invoked and return 422
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer", "int_parsing"])


def test_validate_return_type():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a return type
    @app.get("/")
    def handler() -> int:
        return 123

    LOAD_GW_EVENT["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be 123
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert result["body"] == "123"


def test_validate_return_list():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a return type
    @app.get("/")
    def handler() -> List[int]:
        return [123, 234]

    LOAD_GW_EVENT["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be [123, 234]
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == [123, 234]


def test_validate_return_tuple():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    sample_tuple = (1, 2, 3)

    # WHEN a handler is defined with a return type as Tuple
    @app.get("/")
    def handler() -> Tuple:
        return sample_tuple

    LOAD_GW_EVENT["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a tuple
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == [1, 2, 3]


def test_validate_return_purepath():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    sample_path = PurePath(__file__)

    # WHEN a handler is defined with a return type as string
    # WHEN return value is a PurePath
    @app.get("/")
    def handler() -> str:
        return sample_path.as_posix()

    LOAD_GW_EVENT["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a string
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert result["body"] == sample_path.as_posix()


def test_validate_return_enum():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(Enum):
        name = "powertools"

    # WHEN a handler is defined with a return type as Enum
    @app.get("/")
    def handler() -> Model:
        return Model.name.value

    LOAD_GW_EVENT["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a string
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert result["body"] == "powertools"


def test_validate_return_dataclass():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    @dataclass
    class Model:
        name: str
        age: int

    # WHEN a handler is defined with a return type as dataclass
    @app.get("/")
    def handler() -> Model:
        return Model(name="John", age=30)

    LOAD_GW_EVENT["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_return_model():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a return type as Pydantic model
    @app.get("/")
    def handler() -> Model:
        return Model(name="John", age=30)

    LOAD_GW_EVENT["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_invalid_return_model():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a return type as Pydantic model
    @app.get("/")
    def handler() -> Model:
        return {"name": "John"}  # type: ignore

    LOAD_GW_EVENT["path"] = "/"

    # THEN the handler should be invoked and return 422
    # THEN the body must be a dict
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 422
    assert "missing" in result["body"]


def test_validate_body_param():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Model) -> Model:
        return user

    LOAD_GW_EVENT["httpMethod"] = "POST"
    LOAD_GW_EVENT["path"] = "/"
    LOAD_GW_EVENT["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_body_param_with_invalid_date():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Model) -> Model:
        return user

    LOAD_GW_EVENT["httpMethod"] = "POST"
    LOAD_GW_EVENT["path"] = "/"
    LOAD_GW_EVENT["body"] = "{"  # invalid JSON

    # THEN the handler should be invoked and return 422
    # THEN the body must have the "json_invalid" error message
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 422
    assert "json_invalid" in result["body"]


def test_validate_embed_body_param():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Annotated[Model, Body(embed=True)]) -> Model:
        return user

    LOAD_GW_EVENT["httpMethod"] = "POST"
    LOAD_GW_EVENT["path"] = "/"
    LOAD_GW_EVENT["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 422
    # THEN the body must be a dict
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 422
    assert "missing" in result["body"]

    # THEN the handler should be invoked and return 200
    # THEN the body must be a dict
    LOAD_GW_EVENT["body"] = json.dumps({"user": {"name": "John", "age": 30}})
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200


def test_validate_response_return():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Annotated[Model, Body(embed=True)]) -> Response[Model]:
        return Response(body=user, status_code=200)

    LOAD_GW_EVENT["httpMethod"] = "POST"
    LOAD_GW_EVENT["path"] = "/"
    LOAD_GW_EVENT["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 422
    # THEN the body must be a dict
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 422
    assert "missing" in result["body"]

    # THEN the handler should be invoked and return 200
    # THEN the body must be a dict
    LOAD_GW_EVENT["body"] = json.dumps({"user": {"name": "John", "age": 30}})
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
