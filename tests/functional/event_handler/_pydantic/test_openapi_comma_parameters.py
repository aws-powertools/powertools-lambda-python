import json
from copy import deepcopy
from typing import Annotated

import pytest
from pydantic import BaseModel, ConfigDict, Field

from aws_lambda_powertools.event_handler import (
    ALBResolver,
    APIGatewayHttpResolver,
    APIGatewayRestResolver,
    LambdaFunctionUrlResolver,
    VPCLatticeResolver,
    VPCLatticeV2Resolver,
)
from aws_lambda_powertools.event_handler.openapi.params import Body, Form, Header, Query
from tests.functional.utils import load_event

RESOLVERS = [
    (APIGatewayHttpResolver, "apiGatewayProxyV2Event.json"),
    (LambdaFunctionUrlResolver, "lambdaFunctionUrlEventWithHeaders.json"),
    (APIGatewayRestResolver, "apiGatewayProxyEvent.json"),
    (ALBResolver, "albEvent.json"),
    (VPCLatticeResolver, "vpcLatticeEvent.json"),
    (VPCLatticeV2Resolver, "vpcLatticeV2EventWithHeaders.json"),
]


@pytest.fixture(params=RESOLVERS, ids=lambda entry: entry[0].__name__)
def resolver_event(request):
    resolver, fixture = request.param
    app = resolver(enable_validation=True)
    event = load_event(fixture)
    event.pop("multiValueQueryStringParameters", None)
    event.pop("multiValueHeaders", None)
    event.update(path="/search", rawPath="/search", raw_path="/search", httpMethod="GET", method="GET")
    if "http" in event.get("requestContext", {}):
        event["requestContext"]["http"].update(method="GET", path="/search")
        event["requestContext"]["stage"] = "$default"
    event["headers"] = {}
    event["queryStringParameters"] = {}
    event["query_string_parameters"] = {}
    event["rawQueryString"] = ""
    event["body"] = None
    return app, event


def set_query(app, event, query):
    if isinstance(app, VPCLatticeV2Resolver):
        event["queryStringParameters"] = {key: [value] for key, value in query.items()}
    elif isinstance(app, VPCLatticeResolver):
        event["query_string_parameters"] = query
    else:
        event["queryStringParameters"] = query


@pytest.mark.parametrize("value", ["hello,world", ",hello", "hello,", "hello,, world", "", "plain"])
@pytest.mark.parametrize("location", [Query, Header], ids=["query", "header"])
def test_scalar_parameters_preserve_commas(resolver_event, value, location):
    app, event = resolver_event

    @app.get("/search")
    def handler(search: Annotated[str, location(alias="X-Search")]):
        return {"search": search}

    if location is Header:
        event["headers"] = {"x-search": value}
    else:
        set_query(app, event, {"X-Search": value})
    original_event = deepcopy(event)

    result = app.resolve(event, {})

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"search": value}
    assert event == original_event


@pytest.mark.parametrize("value", ["hello,world", ",hello", "hello,", "hello,, world", ""])
@pytest.mark.parametrize("location", [Query, Header], ids=["query", "header"])
def test_model_parameters_preserve_commas(resolver_event, value, location):
    app, event = resolver_event

    class Params(BaseModel):
        search: str = Field(alias="x-search")

    @app.get("/search")
    def handler(params: Annotated[Params, location()]):
        return params.model_dump()

    if location is Header:
        event["headers"] = {"X-Search": value}
    else:
        set_query(app, event, {"x-search": value})

    result = app.resolve(event, {})

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"search": value}


def test_query_model_preserves_scalar_and_sequence_fields(resolver_event):
    app, event = resolver_event

    class Params(BaseModel):
        model_config = ConfigDict(populate_by_name=True)
        search: str | None = Field(default=None, alias="term")
        tags: list[str] | None = None

    @app.get("/search")
    def handler(params: Annotated[Params, Query()]):
        return params.model_dump()

    set_query(app, event, {"search": "hello, world", "tags": "a,,b"})

    result = app.resolve(event, {})

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"search": "hello, world", "tags": ["a", "", "b"]}


def test_sequence_query_parameters_still_split_commas(resolver_event):
    app, event = resolver_event

    @app.get("/search")
    def handler(tags: Annotated[list[str], Query()]):
        return {"tags": tags}

    set_query(app, event, {"tags": "a, b,,c"})

    result = app.resolve(event, {})

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"tags": ["a", " b", "", "c"]}


@pytest.mark.parametrize("annotation,value", [(int, "1,2"), (float, "1.5,2.5"), (bool, "true,false")])
def test_query_model_validates_the_entire_scalar(resolver_event, annotation, value):
    app, event = resolver_event

    class Params(BaseModel):
        search: annotation

    @app.get("/search")
    def handler(params: Annotated[Params, Query()]):
        pytest.fail("Invalid scalar must not be truncated into a valid value")

    set_query(app, event, {"search": value})

    result = app.resolve(event, {})

    assert result["statusCode"] == 422


@pytest.mark.parametrize("resolver", [APIGatewayHttpResolver, LambdaFunctionUrlResolver])
@pytest.mark.parametrize("model", [False, True], ids=["scalar", "model"])
def test_header_sequences_keep_splitting_commas(resolver, model):
    app = resolver(enable_validation=True)
    event = load_event("apiGatewayProxyV2Event.json")
    event.update(rawPath="/search", body=None)
    event["requestContext"]["http"]["method"] = "GET"
    event["headers"] = {"X-Tags": "a, b,,c"}

    if model:

        class Params(BaseModel):
            tags: list[str] = Field(alias="x-tags")

        @app.get("/search")
        def model_handler(params: Annotated[Params, Header()]):
            return params.model_dump()
    else:

        @app.get("/search")
        def scalar_handler(tags: Annotated[list[str], Header(alias="X-Tags")]):
            return {"tags": tags}

    result = app.resolve(event, {})

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"tags": ["a", " b", "", "c"]}


@pytest.mark.parametrize("resolver", [APIGatewayHttpResolver, LambdaFunctionUrlResolver])
@pytest.mark.parametrize(
    "raw_query,query,expected_status",
    [
        ("search=hello,world", "hello,world", 200),
        ("search=hello%2Cworld", "hello,world", 200),
        ("search=hello&search=world", "hello,world", 422),
        ("%73earch=hello&search=world", "hello,world", 422),
        ("search=&search=world", ",world", 422),
    ],
)
def test_http_v2_distinguishes_repeated_query_values(resolver, raw_query, query, expected_status):
    app = resolver(enable_validation=True)
    event = load_event("apiGatewayProxyV2Event.json")
    event.update(rawPath="/search", rawQueryString=raw_query, body=None)
    event["requestContext"]["http"]["method"] = "GET"
    event["queryStringParameters"] = {"search": query}

    @app.get("/search")
    def handler(search: str):
        return {"search": search}

    result = app.resolve(event, {})

    assert result["statusCode"] == expected_status
    if expected_status == 200:
        assert json.loads(result["body"]) == {"search": query}


@pytest.mark.parametrize("model", [False, True], ids=["scalar", "model"])
@pytest.mark.parametrize("location", [Query, Header], ids=["query", "header"])
@pytest.mark.parametrize("resolver", [APIGatewayRestResolver, ALBResolver])
def test_native_repeated_parameters_keep_existing_behavior(resolver, location, model):
    app = resolver(enable_validation=True)
    event = load_event("albEvent.json" if resolver is ALBResolver else "apiGatewayProxyEvent.json")
    event.update(path="/search", httpMethod="GET")
    event["headers"] = {}
    event["multiValueHeaders"] = {}
    event["queryStringParameters"] = {"search": "ignored"}
    event["multiValueQueryStringParameters"] = {}
    event["body"] = None
    key = "multiValueHeaders" if location is Header else "multiValueQueryStringParameters"
    event[key] = {"SEARCH" if location is Header else "search": ["first", "second"]}

    if model:

        class Params(BaseModel):
            model_config = ConfigDict(populate_by_name=True)
            search: str = Field(alias="term")

        @app.get("/search")
        def model_handler(params: Annotated[Params, location()]):
            return params.model_dump()
    else:

        @app.get("/search")
        def scalar_handler(search: Annotated[str, location()]):
            return {"search": search}

    result = app.resolve(event, {})

    if model:
        assert result["statusCode"] == 200
        assert json.loads(result["body"]) == {"search": "first"}
    else:
        assert result["statusCode"] == 422


@pytest.mark.parametrize("resolver", [APIGatewayRestResolver, ALBResolver])
def test_native_multivalue_query_preserves_literal_commas_and_fallback(resolver):
    app = resolver(enable_validation=True)
    event = load_event("albEvent.json" if resolver is ALBResolver else "apiGatewayProxyEvent.json")
    event.update(path="/search", httpMethod="GET")
    event["queryStringParameters"] = {"search": "ignored", "fallback": "hello,world"}
    event["multiValueQueryStringParameters"] = {"search": ["first,second"], "tags": ["a,b", "c"]}
    event["body"] = None

    @app.get("/search")
    def handler(search: str, fallback: str, tags: Annotated[list[str], Query()]):
        return {"search": search, "fallback": fallback, "tags": tags}

    result = app.resolve(event, {})

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {
        "search": "first,second",
        "fallback": "hello,world",
        "tags": ["a,b", "c"],
    }


@pytest.mark.parametrize("value", ["hello%2Cworld", "hello,world", "hello%2Cworld, again"])
def test_alb_decoding_preserves_commas(value):
    app = ALBResolver(enable_validation=True, decode_query_parameters=True)
    event = load_event("albEvent.json")
    event["path"] = "/search"
    event["body"] = None
    event["queryStringParameters"] = {"%73earch": value}

    @app.get("/search")
    def handler(search: str):
        return {"search": search}

    result = app.resolve(event, {})

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"search": value.replace("%2C", ",")}


def test_alb_decoding_keeps_native_repeated_parameters():
    app = ALBResolver(enable_validation=True, decode_query_parameters=True)
    event = load_event("albEvent.json")
    event["path"] = "/search"
    event["body"] = None
    event["queryStringParameters"] = {"search": "ignored"}
    event["multiValueQueryStringParameters"] = {"%73earch": ["first", "second"]}

    @app.get("/search")
    def handler(search: str):
        return {"search": search}

    result = app.resolve(event, {})

    assert result["statusCode"] == 422


def test_alb_decoding_preserves_precedence_when_parameter_names_collide():
    app = ALBResolver(enable_validation=True, decode_query_parameters=True)
    event = load_event("albEvent.json")
    event["path"] = "/search"
    event["body"] = None
    event["queryStringParameters"] = {"search": "ignored", "%73earch": "hello,world"}
    event["multiValueQueryStringParameters"] = {"search": ["first", "second"]}

    @app.get("/search")
    def handler(search: str):
        return {"search": search}

    result = app.resolve(event, {})

    # The later encoded key wins when ALB decodes the merged parameter mapping.
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"search": "hello,world"}


def test_lattice_v2_keeps_native_repeated_parameters():
    app = VPCLatticeV2Resolver(enable_validation=True)
    event = load_event("vpcLatticeV2EventWithHeaders.json")
    event.update(path="/search", method="GET", body=None)
    event["queryStringParameters"] = {"search": ["first", "second"]}

    @app.get("/search")
    def handler(search: str):
        return {"search": search}

    result = app.resolve(event, {})

    assert result["statusCode"] == 422


@pytest.mark.parametrize("content_type", ["application/json", "application/x-www-form-urlencoded"])
def test_body_scalar_lists_keep_existing_normalization(content_type):
    app = APIGatewayRestResolver(enable_validation=True)
    event = load_event("apiGatewayProxyEvent.json")
    event.update(path="/search", httpMethod="POST", isBase64Encoded=False)
    event["headers"] = {"Content-Type": content_type}
    event["multiValueHeaders"] = {}
    event["queryStringParameters"] = {}
    event["multiValueQueryStringParameters"] = {}
    if content_type == "application/json":
        param = Body(embed=True)
        event["body"] = json.dumps({"search": ["first", "second"]})
    else:
        param = Form()
        event["body"] = "search=first&search=second"

    @app.post("/search")
    def handler(search: Annotated[str, param]):
        return {"search": search}

    result = app.resolve(event, {})

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"search": "first"}
