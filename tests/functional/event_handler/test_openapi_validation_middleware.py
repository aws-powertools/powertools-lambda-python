import json
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
)
from aws_lambda_powertools.event_handler.openapi.params import Body, Header, Query
from aws_lambda_powertools.shared.types import Annotated


def test_validate_scalars(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a scalar parameter
    @app.get("/users/<user_id>")
    def handler(user_id: int):
        print(user_id)

    # sending a number
    gw_event["path"] = "/users/123"

    # THEN the handler should be invoked and return 200
    result = app(gw_event, {})
    assert result["statusCode"] == 200

    # sending a string
    gw_event["path"] = "/users/abc"

    # THEN the handler should be invoked and return 422
    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer", "int_parsing"])


def test_validate_scalars_with_default(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter
    @app.get("/users/<user_id>")
    def handler(user_id: int = 123):
        print(user_id)

    # sending a number
    gw_event["path"] = "/users/123"

    # THEN the handler should be invoked and return 200
    result = app(gw_event, {})
    assert result["statusCode"] == 200

    # sending a string
    gw_event["path"] = "/users/abc"

    # THEN the handler should be invoked and return 422
    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer", "int_parsing"])


def test_validate_scalars_with_default_and_optional(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a default scalar parameter
    @app.get("/users/<user_id>")
    def handler(user_id: int = 123, include_extra: bool = False):
        print(user_id)

    # sending a number
    gw_event["path"] = "/users/123"

    # THEN the handler should be invoked and return 200
    result = app(gw_event, {})
    assert result["statusCode"] == 200

    # sending a string
    gw_event["path"] = "/users/abc"

    # THEN the handler should be invoked and return 422
    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert any(text in result["body"] for text in ["type_error.integer", "int_parsing"])


def test_validate_return_type(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a return type
    @app.get("/")
    def handler() -> int:
        return 123

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be 123
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert result["body"] == "123"


def test_validate_return_list(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined with a return type
    @app.get("/")
    def handler() -> List[int]:
        return [123, 234]

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be [123, 234]
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == [123, 234]


def test_validate_return_tuple(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    sample_tuple = (1, 2, 3)

    # WHEN a handler is defined with a return type as Tuple
    @app.get("/")
    def handler() -> Tuple:
        return sample_tuple

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a tuple
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == [1, 2, 3]


def test_validate_return_purepath(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    sample_path = PurePath(__file__)

    # WHEN a handler is defined with a return type as string
    # WHEN return value is a PurePath
    @app.get("/")
    def handler() -> str:
        return sample_path.as_posix()

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a string
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert result["body"] == sample_path.as_posix()


def test_validate_return_enum(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(Enum):
        name = "powertools"

    # WHEN a handler is defined with a return type as Enum
    @app.get("/")
    def handler() -> Model:
        return Model.name.value

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a string
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert result["body"] == "powertools"


def test_validate_return_dataclass(gw_event):
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

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_return_model(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a return type as Pydantic model
    @app.get("/")
    def handler() -> Model:
        return Model(name="John", age=30)

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_invalid_return_model(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a return type as Pydantic model
    @app.get("/")
    def handler() -> Model:
        return {"name": "John"}  # type: ignore

    gw_event["path"] = "/"

    # THEN the handler should be invoked and return 422
    # THEN the body must be a dict
    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert "missing" in result["body"]


def test_validate_body_param(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Model) -> Model:
        return user

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_body_param_with_stripped_headers(gw_event):
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

    gw_event["httpMethod"] = "POST"
    gw_event["headers"] = {"Content-type": " application/json "}
    gw_event["path"] = "/"
    gw_event["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 200
    # THEN the body must be a JSON object
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_body_param_with_invalid_date(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Model) -> Model:
        return user

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = "{"  # invalid JSON

    # THEN the handler should be invoked and return 422
    # THEN the body must have the "json_invalid" error message
    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert "json_invalid" in result["body"]


def test_validate_embed_body_param(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Annotated[Model, Body(embed=True)]) -> Model:
        return user

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 422
    # THEN the body must be a dict
    result = app(gw_event, {})
    assert result["statusCode"] == 422
    assert "missing" in result["body"]

    # THEN the handler should be invoked and return 200
    # THEN the body must be a dict
    gw_event["body"] = json.dumps({"user": {"name": "John", "age": 30}})
    result = app(gw_event, {})
    assert result["statusCode"] == 200


def test_validate_response_return(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Model) -> Response[Model]:
        return Response(body=user, status_code=200, content_type="application/json")

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = json.dumps({"name": "John", "age": 30})

    # THEN the handler should be invoked and return 200
    # THEN the body must be a dict
    result = app(gw_event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_validate_response_invalid_return(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    # WHEN a handler is defined with a body parameter
    @app.post("/")
    def handler(user: Model) -> Response[Model]:
        return Response(body=user, status_code=200)

    gw_event["httpMethod"] = "POST"
    gw_event["path"] = "/"
    gw_event["body"] = json.dumps({})

    # THEN the handler should be invoked and return 422
    # THEN the body should have the word missing
    result = app(gw_event, {})
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
def test_validation_query_string_with_api_rest_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event,
):
    # GIVEN a APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    gw_event["httpMethod"] = "GET"
    gw_event["path"] = "/users"
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
        gw_event["queryStringParameters"] = None
        gw_event["multiValueQueryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event, {})
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
def test_validation_query_string_with_api_http_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_http,
):
    # GIVEN a APIGatewayHttpResolver with validation enabled
    app = APIGatewayHttpResolver(enable_validation=True)

    gw_event_http["rawPath"] = "/users"
    gw_event_http["requestContext"]["http"]["method"] = "GET"
    gw_event_http["requestContext"]["http"]["path"] = "/users"
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
        gw_event_http["queryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_http, {})
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
def test_validation_query_string_with_alb_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_alb,
):
    # GIVEN a ALBResolver with validation enabled
    app = ALBResolver(enable_validation=True)

    gw_event_alb["path"] = "/users"

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
        gw_event_alb["multiValueQueryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_alb, {})
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
def test_validation_query_string_with_lambda_url_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_lambda_url,
):
    # GIVEN a LambdaFunctionUrlResolver with validation enabled
    app = LambdaFunctionUrlResolver(enable_validation=True)

    gw_event_lambda_url["rawPath"] = "/users"
    gw_event_lambda_url["requestContext"]["http"]["method"] = "GET"
    gw_event_lambda_url["requestContext"]["http"]["path"] = "/users"
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
        gw_event_lambda_url["queryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_lambda_url, {})
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
def test_validation_query_string_with_vpc_lattice_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_vpc_lattice,
):
    # GIVEN a VPCLatticeV2Resolver with validation enabled
    app = VPCLatticeV2Resolver(enable_validation=True)

    gw_event_vpc_lattice["path"] = "/users"

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
        gw_event_vpc_lattice["queryStringParameters"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_vpc_lattice, {})
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
def test_validation_header_with_api_rest_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event,
):
    # GIVEN a APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    gw_event["httpMethod"] = "GET"
    gw_event["path"] = "/users"
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
        gw_event["headers"] = None
        gw_event["multiValueHeaders"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event, {})
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
def test_validation_header_with_http_rest_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_http,
):
    # GIVEN a APIGatewayHttpResolver with validation enabled
    app = APIGatewayHttpResolver(enable_validation=True)

    gw_event_http["rawPath"] = "/users"
    gw_event_http["requestContext"]["http"]["method"] = "GET"
    gw_event_http["requestContext"]["http"]["path"] = "/users"
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
        gw_event_http["headers"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_http, {})
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
def test_validation_header_with_alb_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_alb,
):
    # GIVEN a ALBResolver with validation enabled
    app = ALBResolver(enable_validation=True)

    gw_event_alb["path"] = "/users"
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
        gw_event_alb["multiValueHeaders"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_alb, {})
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
def test_validation_header_with_lambda_url_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_lambda_url,
):
    # GIVEN a LambdaFunctionUrlResolver with validation enabled
    app = LambdaFunctionUrlResolver(enable_validation=True)

    gw_event_lambda_url["rawPath"] = "/users"
    gw_event_lambda_url["requestContext"]["http"]["method"] = "GET"
    gw_event_lambda_url["requestContext"]["http"]["path"] = "/users"
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
        gw_event_lambda_url["headers"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_lambda_url, {})
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
def test_validation_header_with_vpc_lattice_v1_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_vpc_lattice_v1,
):
    # GIVEN a VPCLatticeResolver with validation enabled
    app = VPCLatticeResolver(enable_validation=True)

    gw_event_vpc_lattice_v1["raw_path"] = "/users"
    gw_event_vpc_lattice_v1["method"] = "GET"
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
        gw_event_vpc_lattice_v1["headers"] = None

        @app.get("/users")
        def handler4():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_vpc_lattice_v1, {})
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
def test_validation_header_with_vpc_lattice_v2_resolver(
    handler_func,
    expected_status_code,
    expected_error_text,
    gw_event_vpc_lattice,
):
    # GIVEN a VPCLatticeV2Resolver with validation enabled
    app = VPCLatticeV2Resolver(enable_validation=True)

    gw_event_vpc_lattice["path"] = "/users"
    gw_event_vpc_lattice["method"] = "GET"
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
        gw_event_vpc_lattice["headers"] = None

        @app.get("/users")
        def handler3():
            return None

    # THEN the handler should be invoked with the expected result
    # AND the status code should match the expected_status_code
    result = app(gw_event_vpc_lattice, {})
    assert result["statusCode"] == expected_status_code

    # IF expected_error_text is provided, THEN check for its presence in the response body
    if expected_error_text:
        assert any(text in result["body"] for text in expected_error_text)


def test_validation_with_alias(gw_event):
    # GIVEN a REST API V2 proxy type event
    app = APIGatewayRestResolver(enable_validation=True)

    # GIVEN that it has a multiple parameters called "parameter1"
    gw_event["queryStringParameters"] = {
        "parameter1": "value1,value2",
    }

    @app.get("/my/path")
    def my_path(
        parameter: Annotated[Optional[str], Query(alias="parameter1")] = None,
    ) -> str:
        assert parameter == "value1"
        return parameter

    result = app(gw_event, {})
    assert result["statusCode"] == 200


def test_validation_with_http_single_param(gw_event_http):
    # GIVEN a HTTP API V2 proxy type event
    app = APIGatewayHttpResolver(enable_validation=True)

    # GIVEN that it has a single parameter called "parameter2"
    gw_event_http["queryStringParameters"] = {
        "parameter1": "value1,value2",
        "parameter2": "value",
    }

    # WHEN a handler is defined with a single parameter
    @app.post("/my/path")
    def my_path(
        parameter2: str,
    ) -> str:
        assert parameter2 == "value"
        return parameter2

    # THEN the handler should be invoked and return 200
    result = app(gw_event_http, {})
    assert result["statusCode"] == 200
