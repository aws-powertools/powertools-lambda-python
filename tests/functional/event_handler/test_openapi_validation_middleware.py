import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePath
from typing import List, Optional, Tuple

import pytest
from pydantic import BaseModel

from aws_lambda_powertools.event_handler import (
    ALBResolver,
    APIGatewayHttpResolver,
    APIGatewayRestResolver,
    LambdaFunctionUrlResolver,
    Response,
    VPCLatticeResolver,
    VPCLatticeV2Resolver,
    content_types,
)
from aws_lambda_powertools.event_handler.openapi.params import Body, Header, Query
from aws_lambda_powertools.shared.types import Annotated
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from tests.functional.utils import load_event

LOAD_GW_EVENT = load_event("apiGatewayProxyEvent.json")
LOAD_GW_EVENT_HTTP = load_event("apiGatewayProxyV2Event.json")
LOAD_GW_EVENT_ALB = load_event("albMultiValueQueryStringEvent.json")
LOAD_GW_EVENT_LAMBDA_URL = load_event("lambdaFunctionUrlEventWithHeaders.json")
LOAD_GW_EVENT_VPC_LATTICE = load_event("vpcLatticeV2EventWithHeaders.json")
LOAD_GW_EVENT_VPC_LATTICE_V1 = load_event("vpcLatticeEvent.json")


def test_validate_scalars():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a scalar parameter
    @app.get("/users/<user_id>")
    def handler(user_id: int):
        print(user_id)

    # sending a number
    event = deepcopy(LOAD_GW_EVENT)
    event["path"] = "/users/123"

    # THEN the handler should be invoked and return 200
    result = app(event, {})
    assert result["statusCode"] == 200

    # sending a string
    event["path"] = "/users/abc"

    # THEN the handler should be invoked and return 422
    result = app(event, {})
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
    event = deepcopy(LOAD_GW_EVENT)
    event["path"] = "/users/123"

    # THEN the handler should be invoked and return 200
    result = app(event, {})
    assert result["statusCode"] == 200

    # sending a string
    event["path"] = "/users/abc"

    # THEN the handler should be invoked and return 422
    result = app(event, {})
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
    event = deepcopy(LOAD_GW_EVENT)
    event["path"] = "/users/123"

    # THEN the handler should be invoked and return 200
    result = app(event, {})
    assert result["statusCode"] == 200

    # sending a string
    event["path"] = "/users/abc"

    # THEN the handler should be invoked and return 422
    result = app(event, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer", "int_parsing"])


def test_validate_return_type():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a return type
    @app.get("/")
    def handler() -> int:
        return 123

    event = deepcopy(LOAD_GW_EVENT)
    event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be 123
    result = app(event, {})
    assert result["statusCode"] == 200
    assert result["body"] == "123"


def test_validate_return_list():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a return type
    @app.get("/")
    def handler() -> List[int]:
        return [123, 234]

    event = deepcopy(LOAD_GW_EVENT)
    event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be [123, 234]
    result = app(event, {})
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

    event = deepcopy(LOAD_GW_EVENT)
    event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a tuple
    result = app(event, {})
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

    event = deepcopy(LOAD_GW_EVENT)
    event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a string
    result = app(event, {})
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

    event = deepcopy(LOAD_GW_EVENT)
    event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a string
    result = app(event, {})
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

    event = deepcopy(LOAD_GW_EVENT)
    event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(event, {})
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

    event = deepcopy(LOAD_GW_EVENT)
    event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(event, {})
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

    event = deepcopy(LOAD_GW_EVENT)
    event["path"] = "/"

    # THEN the handler should be invoked and return 422
    # THEN the body must be a dict
    result = app(event, {})
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

    event = deepcopy(LOAD_GW_EVENT)
    event["httpMethod"] = "POST"
    event["path"] = "/"
    event["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_body_param_with_stripped_headers():
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    # WHEN headers has spaces
    @app.post("/")
    def handler(user: Model) -> Model:
        return user

    event = deepcopy(LOAD_GW_EVENT)
    event["httpMethod"] = "POST"
    event["headers"] = {"Content-type": " application/json "}
    event["path"] = "/"
    event["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(event, {})
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

    event = deepcopy(LOAD_GW_EVENT)
    event["httpMethod"] = "POST"
    event["path"] = "/"
    event["body"] = "{"  # invalid JSON

    # THEN the handler should be invoked and return 422
    # THEN the body must have the "json_invalid" error message
    result = app(event, {})
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

    event = deepcopy(LOAD_GW_EVENT)
    event["httpMethod"] = "POST"
    event["path"] = "/"
    event["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 422
    # THEN the body must be a dict
    result = app(event, {})
    assert result["statusCode"] == 422
    assert "missing" in result["body"]

    # THEN the handler should be invoked and return 200
    # THEN the body must be a dict
    event["body"] = json.dumps({"user": {"name": "John", "age": 30}})
    result = app(event, {})
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

    event = deepcopy(LOAD_GW_EVENT)
    event["httpMethod"] = "POST"
    event["path"] = "/"
    event["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 200
    # THEN the body must be a dict
    result = app(event, {})
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

    event = deepcopy(LOAD_GW_EVENT)
    event["httpMethod"] = "POST"
    event["path"] = "/"
    event["body"] = json.dumps({})

    # THEN the handler should be invoked and return 422
    # THEN the body should have the word missing
    result = app(event, {})
    assert result["statusCode"] == 422
    assert "missing" in result["body"]


########### TEST WITH QUERY PARAMS
@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_without_query_params", 200, None),
    ],
)
def test_validation_query_string_with_api_rest_resolver(handler_func, expected_status_code, expected_error_text):
    # GIVEN a APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    event = deepcopy(LOAD_GW_EVENT)
    event["httpMethod"] = "GET"
    event["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(parameter1: Annotated[List[str], Query()], parameter2: str):
            print(parameter2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(parameter1: Annotated[List[int], Query()], parameter2: str):
            print(parameter2)

    # Define handler3 without params
    if handler_func == "handler3_without_query_params":
        event["queryStringParameters"] = None
        event["multiValueQueryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(event, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_without_query_params", 200, None),
    ],
)
def test_validation_query_string_with_api_http_resolver(handler_func, expected_status_code, expected_error_text):
    # GIVEN a APIGatewayHttpResolver with validation enabled
    app = APIGatewayHttpResolver(enable_validation=True)

    event = deepcopy(LOAD_GW_EVENT_HTTP)
    event["rawPath"] = "/users"
    event["requestContext"]["http"]["method"] = "GET"
    event["requestContext"]["http"]["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(parameter1: Annotated[List[str], Query()], parameter2: str):
            print(parameter2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(parameter1: Annotated[List[int], Query()], parameter2: str):
            print(parameter2)

    # Define handler3 without params
    if handler_func == "handler3_without_query_params":
        event["queryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(event, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_without_query_params", 200, None),
    ],
)
def test_validation_query_string_with_alb_resolver(handler_func, expected_status_code, expected_error_text):
    # GIVEN a ALBResolver with validation enabled
    app = ALBResolver(enable_validation=True)

    event = deepcopy(LOAD_GW_EVENT_ALB)
    event["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(parameter1: Annotated[List[str], Query()], parameter2: str):
            print(parameter2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(parameter1: Annotated[List[int], Query()], parameter2: str):
            print(parameter2)

    # Define handler3 without params
    if handler_func == "handler3_without_query_params":
        event["multiValueQueryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(event, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_without_query_params", 200, None),
    ],
)
def test_validation_query_string_with_lambda_url_resolver(handler_func, expected_status_code, expected_error_text):
    # GIVEN a LambdaFunctionUrlResolver with validation enabled
    app = LambdaFunctionUrlResolver(enable_validation=True)

    event = deepcopy(LOAD_GW_EVENT_LAMBDA_URL)
    event["rawPath"] = "/users"
    event["requestContext"]["http"]["method"] = "GET"
    event["requestContext"]["http"]["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(parameter1: Annotated[List[str], Query()], parameter2: str):
            print(parameter2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(parameter1: Annotated[List[int], Query()], parameter2: str):
            print(parameter2)

    # Define handler3 without params
    if handler_func == "handler3_without_query_params":
        event["queryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(event, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_without_query_params", 200, None),
    ],
)
def test_validation_query_string_with_vpc_lattice_resolver(handler_func, expected_status_code, expected_error_text):
    # GIVEN a VPCLatticeV2Resolver with validation enabled
    app = VPCLatticeV2Resolver(enable_validation=True)

    event = deepcopy(LOAD_GW_EVENT_VPC_LATTICE)
    event["path"] = "/users"

    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(parameter1: Annotated[List[str], Query()], parameter2: str):
            print(parameter2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(parameter1: Annotated[List[int], Query()], parameter2: str):
            print(parameter2)

    # Define handler3 without params
    if handler_func == "handler3_without_query_params":
        event["queryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(event, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


########### TEST WITH HEADER PARAMS
@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_with_uppercase_params", 200, None),
        ("handler4_without_header_params", 200, None),
    ],
)
def test_validation_header_with_api_rest_resolver(handler_func, expected_status_code, expected_error_text):
    # GIVEN a APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    event = deepcopy(LOAD_GW_EVENT)
    event["httpMethod"] = "GET"
    event["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[str], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(header2: Annotated[List[int], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler3 with uppercase parameters
    if handler_func == "handler3_with_uppercase_params":

        @app.get("/users")
        def handler3(
            header2: Annotated[List[str], Header(name="Header2")],
            header1: Annotated[str, Header(name="Header1")],
        ):
            print(header2)

    # Define handler4 without params
    if handler_func == "handler4_without_header_params":
        event["headers"] = None
        event["multiValueHeaders"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(event, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_with_uppercase_params", 200, None),
        ("handler4_without_header_params", 200, None),
    ],
)
def test_validation_header_with_http_rest_resolver(handler_func, expected_status_code, expected_error_text):
    # GIVEN a APIGatewayHttpResolver with validation enabled
    app = APIGatewayHttpResolver(enable_validation=True)

    event = deepcopy(LOAD_GW_EVENT_HTTP)
    event["rawPath"] = "/users"
    event["requestContext"]["http"]["method"] = "GET"
    event["requestContext"]["http"]["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[str], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(header2: Annotated[List[int], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler3 with uppercase parameters
    if handler_func == "handler3_with_uppercase_params":

        @app.get("/users")
        def handler3(
            header2: Annotated[List[str], Header(name="Header2")],
            header1: Annotated[str, Header(name="Header1")],
        ):
            print(header2)

    # Define handler4 without params
    if handler_func == "handler4_without_header_params":
        event["headers"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(event, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_with_uppercase_params", 200, None),
        ("handler4_without_header_params", 200, None),
    ],
)
def test_validation_header_with_alb_resolver(handler_func, expected_status_code, expected_error_text):
    # GIVEN a ALBResolver with validation enabled
    app = ALBResolver(enable_validation=True)

    event = deepcopy(LOAD_GW_EVENT_ALB)
    event["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[str], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(header2: Annotated[List[int], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler3 with uppercase parameters
    if handler_func == "handler3_with_uppercase_params":

        @app.get("/users")
        def handler3(
            header2: Annotated[List[str], Header(name="Header2")],
            header1: Annotated[str, Header(name="Header1")],
        ):
            print(header2)

    # Define handler4 without params
    if handler_func == "handler4_without_header_params":
        event["multiValueHeaders"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(event, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_with_uppercase_params", 200, None),
        ("handler4_without_header_params", 200, None),
    ],
)
def test_validation_header_with_lambda_url_resolver(handler_func, expected_status_code, expected_error_text):
    # GIVEN a LambdaFunctionUrlResolver with validation enabled
    app = LambdaFunctionUrlResolver(enable_validation=True)

    event = deepcopy(LOAD_GW_EVENT_LAMBDA_URL)
    event["rawPath"] = "/users"
    event["requestContext"]["http"]["method"] = "GET"
    event["requestContext"]["http"]["path"] = "/users"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[str], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(header2: Annotated[List[int], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler3 with uppercase parameters
    if handler_func == "handler3_with_uppercase_params":

        @app.get("/users")
        def handler3(
            header2: Annotated[List[str], Header(name="Header2")],
            header1: Annotated[str, Header(name="Header1")],
        ):
            print(header2)

    # Define handler4 without params
    if handler_func == "handler4_without_header_params":
        event["headers"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(event, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_with_uppercase_params", 200, None),
        ("handler4_without_header_params", 200, None),
    ],
)
def test_validation_header_with_vpc_lattice_v1_resolver(handler_func, expected_status_code, expected_error_text):
    # GIVEN a VPCLatticeResolver with validation enabled
    app = VPCLatticeResolver(enable_validation=True)

    event = deepcopy(LOAD_GW_EVENT_VPC_LATTICE_V1)
    event["raw_path"] = "/users"
    event["method"] = "GET"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[str], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler2(header2: Annotated[List[int], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler3 with uppercase parameters
    if handler_func == "handler3_with_uppercase_params":

        @app.get("/users")
        def handler3(
            header2: Annotated[List[str], Header(name="Header2")],
            header1: Annotated[str, Header(name="Header1")],
        ):
            print(header2)

    # Define handler4 without params
    if handler_func == "handler4_without_header_params":
        event["headers"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(event, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


@pytest.mark.parametrize(
    "handler_func, expected_status_code, expected_error_text",
    [
        ("handler1_with_correct_params", 200, None),
        ("handler2_with_wrong_params", 422, "['type_error.integer', 'int_parsing']"),
        ("handler3_with_uppercase_params", 200, None),
        ("handler4_without_header_params", 200, None),
    ],
)
def test_validation_header_with_vpc_lattice_v2_resolver(handler_func, expected_status_code, expected_error_text):
    # GIVEN a VPCLatticeV2Resolver with validation enabled
    app = VPCLatticeV2Resolver(enable_validation=True)

    event = deepcopy(LOAD_GW_EVENT_VPC_LATTICE)
    event["path"] = "/users"
    event["method"] = "GET"
    # WHEN a handler is defined with various parameters and routes

    # Define handler1 with correct params
    if handler_func == "handler1_with_correct_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[str], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler2 with wrong params
    if handler_func == "handler2_with_wrong_params":

        @app.get("/users")
        def handler1(header2: Annotated[List[int], Header()], header1: Annotated[str, Header()]):
            print(header2)

    # Define handler3 with uppercase parameters
    if handler_func == "handler3_with_uppercase_params":

        @app.get("/users")
        def handler3(
            header2: Annotated[List[str], Header(name="Header2")],
            header1: Annotated[str, Header(name="Header1")],
        ):
            print(header2)

    # Define handler4 without params
    if handler_func == "handler4_without_header_params":
        event["headers"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(event, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


def test_validation_with_alias():
    # GIVEN a REST API V2 proxy type event
    app = APIGatewayRestResolver(enable_validation=True)
    event = deepcopy(LOAD_GW_EVENT)

    class FunkyTown(BaseModel):
        parameter: str

    @app.get("/my/path")
    def my_path(
        parameter: Annotated[Optional[str], Query(alias="parameter1")] = None,
    ) -> Response[FunkyTown]:
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        assert parameter == "value1"
        return Response(200, content_types.APPLICATION_JSON, FunkyTown(parameter=parameter))

    result = app(event, {})
    assert result["statusCode"] == 200


def test_validation_with_http_single_param():
    # GIVEN a HTTP API V2 proxy type event
    app = APIGatewayHttpResolver(enable_validation=True)
    event = deepcopy(LOAD_GW_EVENT_HTTP)

    class FunkyTown(BaseModel):
        parameter: str

    # WHEN a handler is defined with a single parameter
    @app.post("/my/path")
    def my_path(
        parameter2: str,
    ) -> Response[FunkyTown]:
        assert parameter2 == "value"
        return Response(200, content_types.APPLICATION_JSON, FunkyTown(parameter=parameter2))

    # THEN the handler should be invoked and return 200
    result = app(event, {})
    assert result["statusCode"] == 200
