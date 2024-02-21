import json

import pytest

from tests.functional.utils import load_event


@pytest.fixture
def json_dump():
    # our serializers reduce length to save on costs; fixture to replicate separators
    return lambda obj: json.dumps(obj, separators=(",", ":"))


@pytest.fixture
def validation_schema():
    return {
        "$schema": "https://json-schema.org/draft-07/schema",
        "$id": "https://example.com/example.json",
        "type": "object",
        "title": "Sample schema",
        "description": "The root schema comprises the entire JSON document.",
        "examples": [{"message": "hello world", "username": "lessa"}],
        "required": ["message", "username"],
        "properties": {
            "message": {
                "$id": "#/properties/message",
                "type": "string",
                "title": "The message",
                "examples": ["hello world"],
            },
            "username": {
                "$id": "#/properties/username",
                "type": "string",
                "title": "The username",
                "examples": ["lessa"],
            },
        },
    }


@pytest.fixture
def raw_event():
    return {"message": "hello hello", "username": "blah blah"}


@pytest.fixture
def gw_event():
    return load_event("apiGatewayProxyEvent.json")


@pytest.fixture
def gw_event_http():
    return load_event("apiGatewayProxyV2Event.json")


@pytest.fixture
def gw_event_alb():
    return load_event("albMultiValueQueryStringEvent.json")


@pytest.fixture
def gw_event_lambda_url():
    return load_event("lambdaFunctionUrlEventWithHeaders.json")


@pytest.fixture
def gw_event_vpc_lattice():
    return load_event("vpcLatticeV2EventWithHeaders.json")


@pytest.fixture
def gw_event_vpc_lattice_v1():
    return load_event("vpcLatticeEvent.json")
