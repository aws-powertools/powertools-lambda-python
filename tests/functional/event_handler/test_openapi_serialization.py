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
