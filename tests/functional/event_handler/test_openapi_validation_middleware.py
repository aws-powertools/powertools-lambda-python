import json
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePath
from typing import List, Tuple

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import (
    ALBResolver,
    APIGatewayHttpResolver,
    APIGatewayRestResolver,
    LambdaFunctionUrlResolver,
    Response,
    VPCLatticeV2Resolver,
)
from aws_lambda_powertools.event_handler.openapi.params import Body, Query
from aws_lambda_powertools.shared.types import Annotated
from tests.functional.utils import load_event

LOAD_GW_EVENT = load_event("apiGatewayProxyEvent.json")
LOAD_GW_EVENT_HTTP = load_event("apiGatewayProxyV2Event.json")
LOAD_GW_EVENT_ALB = load_event("albMultiValueQueryStringEvent.json")
LOAD_GW_EVENT_LAMBDA_URL = load_event("lambdaFunctionUrlEventWithHeaders.json")
LOAD_GW_EVENT_VPC_LATTICE = load_event("vpcLatticeV2EventWithHeaders.json")


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
    def handler(user: Model) -> Response[Model]:
        return Response(body=user, status_code=200, content_type="application/json")

    LOAD_GW_EVENT["httpMethod"] = "POST"
    LOAD_GW_EVENT["path"] = "/"
    LOAD_GW_EVENT["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 200
    # THEN the body must be a dict
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_response_invalid_return():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Model) -> Response[Model]:
        return Response(body=user, status_code=200)

    LOAD_GW_EVENT["httpMethod"] = "POST"
    LOAD_GW_EVENT["path"] = "/"
    LOAD_GW_EVENT["body"] = json.dumps({})

    # THEN the handler should be invoked and return 422
    # THEN the body should have the word missing
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 422
    assert "missing" in result["body"]


def test_validate_rest_api_resolver_with_multi_query_values():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter and a list
    @app.get("/users")
    def handler(parameter1: Annotated[List[str], Query()], parameter2: str):
        print(parameter2)

    LOAD_GW_EVENT["httpMethod"] = "GET"
    LOAD_GW_EVENT["path"] = "/users"

    # THEN the handler should be invoked and return 200
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 200


def test_validate_rest_api_resolver_with_multi_query_values_fail():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter and a list with wrong type
    @app.get("/users")
    def handler(parameter1: Annotated[List[int], Query()], parameter2: str):
        print(parameter2)

    LOAD_GW_EVENT["httpMethod"] = "GET"
    LOAD_GW_EVENT["path"] = "/users"

    # THEN the handler should be invoked and return 422
    result = app(LOAD_GW_EVENT, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer"])


def test_validate_http_resolver_with_multi_query_values():
    # GIVEN an APIGatewayHttpResolver with validation enabled
    app = APIGatewayHttpResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter and a list
    @app.get("/users")
    def handler(parameter1: Annotated[List[str], Query()], parameter2: str):
        print(parameter2)

    LOAD_GW_EVENT_HTTP["rawPath"] = "/users"
    LOAD_GW_EVENT_HTTP["requestContext"]["http"]["method"] = "GET"
    LOAD_GW_EVENT_HTTP["requestContext"]["http"]["path"] = "/users"

    # THEN the handler should be invoked and return 200
    result = app(LOAD_GW_EVENT_HTTP, {})
    assert result["statusCode"] == 200


def test_validate_http_resolver_with_multi_query_values_fail():
    # GIVEN an APIGatewayHttpResolver with validation enabled
    app = APIGatewayHttpResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter and a list with wrong type
    @app.get("/users")
    def handler(parameter1: Annotated[List[int], Query()], parameter2: str):
        print(parameter2)

    LOAD_GW_EVENT_HTTP["rawPath"] = "/users"
    LOAD_GW_EVENT_HTTP["requestContext"]["http"]["method"] = "GET"
    LOAD_GW_EVENT_HTTP["requestContext"]["http"]["path"] = "/users"

    # THEN the handler should be invoked and return 422
    result = app(LOAD_GW_EVENT_HTTP, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer"])


def test_validate_alb_resolver_with_multi_query_values():
    # GIVEN an ALBResolver with validation enabled
    app = ALBResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter and a list
    @app.get("/users")
    def handler(parameter1: Annotated[List[str], Query()], parameter2: str):
        print(parameter2)

    LOAD_GW_EVENT_ALB["path"] = "/users"

    # THEN the handler should be invoked and return 200
    result = app(LOAD_GW_EVENT_ALB, {})
    assert result["statusCode"] == 200


def test_validate_alb_resolver_with_multi_query_values_fail():
    # GIVEN an ALBResolver with validation enabled
    app = ALBResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter and a list with wrong type
    @app.get("/users")
    def handler(parameter1: Annotated[List[int], Query()], parameter2: str):
        print(parameter2)

    LOAD_GW_EVENT_ALB["path"] = "/users"

    # THEN the handler should be invoked and return 422
    result = app(LOAD_GW_EVENT_ALB, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer"])


def test_validate_lambda_url_resolver_with_multi_query_values():
    # GIVEN an LambdaFunctionUrlResolver with validation enabled
    app = LambdaFunctionUrlResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter and a list
    @app.get("/users")
    def handler(parameter1: Annotated[List[str], Query()], parameter2: str):
        print(parameter2)

    LOAD_GW_EVENT_LAMBDA_URL["rawPath"] = "/users"
    LOAD_GW_EVENT_LAMBDA_URL["requestContext"]["http"]["method"] = "GET"
    LOAD_GW_EVENT_LAMBDA_URL["requestContext"]["http"]["path"] = "/users"

    # THEN the handler should be invoked and return 200
    result = app(LOAD_GW_EVENT_LAMBDA_URL, {})
    assert result["statusCode"] == 200


def test_validate__lambda_url_resolver_with_multi_query_values_fail():
    # GIVEN an LambdaFunctionUrlResolver with validation enabled
    app = LambdaFunctionUrlResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter and a list with wrong type
    @app.get("/users")
    def handler(parameter1: Annotated[List[int], Query()], parameter2: str):
        print(parameter2)

    LOAD_GW_EVENT_LAMBDA_URL["rawPath"] = "/users"
    LOAD_GW_EVENT_LAMBDA_URL["requestContext"]["http"]["method"] = "GET"
    LOAD_GW_EVENT_LAMBDA_URL["requestContext"]["http"]["path"] = "/users"

    # THEN the handler should be invoked and return 422
    result = app(LOAD_GW_EVENT_LAMBDA_URL, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer"])


def test_validate_vpc_lattice_resolver_with_multi_query_values():
    # GIVEN an VPCLatticeV2Resolver with validation enabled
    app = VPCLatticeV2Resolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter and a list
    @app.get("/users")
    def handler(parameter1: Annotated[List[str], Query()], parameter2: str):
        print(parameter2)

    LOAD_GW_EVENT_VPC_LATTICE["path"] = "/users"

    # THEN the handler should be invoked and return 200
    result = app(LOAD_GW_EVENT_VPC_LATTICE, {})
    assert result["statusCode"] == 200


def test_validate_vpc_lattice_resolver_with_multi_query_values_fail():
    # GIVEN an VPCLatticeV2Resolver with validation enabled
    app = VPCLatticeV2Resolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter and a list with wrong type
    @app.get("/users")
    def handler(parameter1: Annotated[List[int], Query()], parameter2: str):
        print(parameter2)

    LOAD_GW_EVENT_VPC_LATTICE["path"] = "/users"

    # THEN the handler should be invoked and return 422
    result = app(LOAD_GW_EVENT_VPC_LATTICE, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer"])
