import json

import fastjsonschema
import pytest

from aws_lambda_powertools.event_handler.openapi.models import APIKey, APIKeyIn
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


@pytest.fixture(scope="session")
def pydanticv1_only():
    from pydantic import __version__

    version = __version__.split(".")
    if version[0] != "1":
        pytest.skip("pydanticv1 test only")


@pytest.fixture(scope="session")
def pydanticv2_only():
    from pydantic import __version__

    version = __version__.split(".")
    if version[0] != "2":
        pytest.skip("pydanticv2 test only")


@pytest.fixture(scope="session")
def openapi30_schema():
    from urllib.request import urlopen

    f = urlopen("https://spec.openapis.org/oas/3.0/schema/2021-09-28")
    data = json.loads(f.read().decode("utf-8"))
    return fastjsonschema.compile(
        data,
        use_formats=False,
    )


@pytest.fixture(scope="session")
def openapi31_schema():
    from urllib.request import urlopen

    f = urlopen("https://spec.openapis.org/oas/3.1/schema/2022-10-07")
    data = json.loads(f.read().decode("utf-8"))
    return fastjsonschema.compile(
        data,
        use_formats=False,
    )


@pytest.fixture
def security_scheme():
    return {"apiKey": APIKey(name="X-API-KEY", description="API Key", in_=APIKeyIn.header)}


@pytest.fixture
def openapi_extension_integration_detail():
    return {
        "type": "aws",
        "httpMethod": "POST",
        "uri": "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/..integration/invocations",
        "responses": {"default": {"statusCode": "200"}},
        "passthroughBehavior": "when_no_match",
        "contentHandling": "CONVERT_TO_TEXT",
    }


@pytest.fixture
def openapi_extension_validator_detail():
    return "Validate body, query string parameters, and headers"
