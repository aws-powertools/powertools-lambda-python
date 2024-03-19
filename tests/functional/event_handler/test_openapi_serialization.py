import json
from typing import Dict

import pytest

from aws_lambda_powertools.event_handler import APIGatewayRestResolver


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
    class CustomClass(object):
        __slots__ = []

    # GIVEN a handler that returns an instance of that class
    @app.get("/my/path")
    def handler():
        return CustomClass()

    # WHEN we invoke the handler
    response = app(gw_event, {})

    # THEN we the custom serializer should be used
    assert response["body"] == "hello world"
