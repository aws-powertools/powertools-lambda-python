import json
from dataclasses import dataclass
from typing import Dict, Optional, Set

import pytest
from pydantic import BaseModel

from aws_lambda_powertools.event_handler import APIGatewayRestResolver


@dataclass
class Person:
    name: str
    birth_date: str
    scores: Set[int]


def test_openapi_duplicated_serialization():
    # GIVEN APIGatewayRestResolver is initialized with enable_validation=True
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN we have duplicated operations
    @app.get("/")
    def handler():
        pass

    @app.get("/")
    def handler():  # noqa: F811
        pass

    # THEN we should get a warning
    with pytest.warns(UserWarning, match="Duplicate Operation*"):
        app.get_openapi_schema()


def test_openapi_serialize_json():
    # GIVEN APIGatewayRestResolver is initialized with enable_validation=True
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/")
    def handler():
        pass

    # WHEN we serialize as json_schema
    schema = json.loads(app.get_openapi_json_schema())

    # THEN we should get a dictionary
    assert isinstance(schema, Dict)


def test_openapi_serialize_other(gw_event):
    # GIVEN a custom serializer
    def serializer(_):
        return "hello world"

    # GIVEN APIGatewayRestResolver is initialized with enable_validation=True and the custom serializer
    app = APIGatewayRestResolver(enable_validation=True, serializer=serializer)

    # GIVEN a custom class
    class CustomClass:
        __slots__ = []

    # GIVEN a handler that returns an instance of that class
    @app.get("/my/path")
    def handler():
        return CustomClass()

    # WHEN we invoke the handler
    response = app(gw_event, {})

    # THEN we the custom serializer should be used
    assert response["body"] == "hello world"


def test_valid_model_returned_for_optional_type(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    class Model(BaseModel):
        name: str
        age: int

    @app.get("/valid_optional")
    def handler_valid_optional() -> Optional[Model]:
        return Model(name="John", age=30)

    # WHEN returning a valid model for an Optional type
    gw_event["path"] = "/valid_optional"
    result = app(gw_event, {})

    # THEN it should succeed and return the serialized model
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "John", "age": 30}


def test_serialize_response_without_field(gw_event):
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler is defined without return type annotation
    @app.get("/test")
    def handler():
        return {"message": "Hello, World!"}

    gw_event["path"] = "/test"

    # THEN the handler should be invoked and return 200
    # AND the body must be a JSON object
    response = app(gw_event, None)
    assert response["statusCode"] == 200
    assert response["body"] == '{"message":"Hello, World!"}'


def test_serialize_response_list(gw_event):
    """Test serialization of list responses containing complex types"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler returns a list containing various types
    @app.get("/test")
    def handler():
        return [{"set": [1, 2, 3]}, {"simple": "value"}]

    gw_event["path"] = "/test"

    # THEN the response should be properly serialized
    response = app(gw_event, None)
    assert response["statusCode"] == 200
    assert response["body"] == '[{"set":[1,2,3]},{"simple":"value"}]'


def test_serialize_response_nested_dict(gw_event):
    """Test serialization of nested dictionary responses"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler returns a nested dictionary with complex types
    @app.get("/test")
    def handler():
        return {"nested": {"date": "2000-01-01", "set": [1, 2, 3]}, "simple": "value"}

    gw_event["path"] = "/test"

    # THEN the response should be properly serialized
    response = app(gw_event, None)
    assert response["statusCode"] == 200
    assert response["body"] == '{"nested":{"date":"2000-01-01","set":[1,2,3]},"simple":"value"}'


def test_serialize_response_dataclass(gw_event):
    """Test serialization of dataclass responses"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler returns a dataclass instance
    @app.get("/test")
    def handler():
        return Person(name="John Doe", birth_date="1990-01-01", scores=[95, 87, 91])

    gw_event["path"] = "/test"

    # THEN the response should be properly serialized
    response = app(gw_event, None)
    assert response["statusCode"] == 200
    assert response["body"] == '{"name":"John Doe","birth_date":"1990-01-01","scores":[95,87,91]}'


def test_serialize_response_mixed_types(gw_event):
    """Test serialization of mixed type responses"""
    # GIVEN an APIGatewayRestResolver with validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # WHEN a handler returns a response with mixed types
    @app.get("/test")
    def handler():
        person = Person(name="John Doe", birth_date="1990-01-01", scores=[95, 87, 91])
        return {
            "person": person,
            "records": [{"date": "2000-01-01"}, {"set": [1, 2, 3]}],
            "metadata": {"processed_at": "2050-01-01", "tags": ["tag1", "tag2"]},
        }

    gw_event["path"] = "/test"

    # THEN the response should be properly serialized
    response = app(gw_event, None)
    assert response["statusCode"] == 200
    expected = {
        "person": {"name": "John Doe", "birth_date": "1990-01-01", "scores": [95, 87, 91]},
        "records": [{"date": "2000-01-01"}, {"set": [1, 2, 3]}],
        "metadata": {"processed_at": "2050-01-01", "tags": ["tag1", "tag2"]},
    }
    assert json.loads(response["body"]) == expected
