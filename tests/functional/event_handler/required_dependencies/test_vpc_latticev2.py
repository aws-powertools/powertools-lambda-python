from __future__ import annotations

import asyncio
import json

from aws_lambda_powertools.event_handler import (
    Response,
    VPCLatticeV2Resolver,
    content_types,
)
from aws_lambda_powertools.event_handler.api_gateway import CORSConfig
from aws_lambda_powertools.utilities.data_classes import VPCLatticeEventV2
from tests.functional.utils import load_event


def test_vpclatticev2_event():
    # GIVEN a VPC Lattice event
    app = VPCLatticeV2Resolver()

    @app.get("/newpath")
    def foo():
        assert isinstance(app.current_event, VPCLatticeEventV2)
        assert app.lambda_context == {}
        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler
    result = app(load_event("vpcLatticeV2Event.json"), {})

    # THEN process event correctly
    # AND set the current_event type as VPCLatticeEvent
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == content_types.TEXT_HTML
    assert result["body"] == "foo"


def test_vpclatticev2_event_path_trailing_slash(json_dump):
    # GIVEN a VPC Lattice event
    app = VPCLatticeV2Resolver()

    @app.get("/newpath")
    def foo():
        assert isinstance(app.current_event, VPCLatticeEventV2)
        assert app.lambda_context == {}
        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler using path with trailing "/"
    result = app(load_event("vpcLatticeEventV2PathTrailingSlash.json"), {})

    # THEN
    assert result["statusCode"] == 404
    assert result["headers"]["Content-Type"] == content_types.APPLICATION_JSON
    expected = {"statusCode": 404, "message": "Not found"}
    assert result["body"] == json_dump(expected)


def test_vpclatticev2_event_with_query_string():
    # GIVEN an event captured from a VPC Lattice V2 target group, whose path carries the query string
    app = VPCLatticeV2Resolver()

    @app.post("/echo")
    def echo():
        return {"query": app.current_event.query_string_parameters, "body": app.current_event.json_body}

    # WHEN calling the event handler
    result = app(load_event("vpcLatticeV2EventWithQueryString.json"), {})

    # THEN the route matches the path without the query string
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {
        "query": {"QS1": "value1,value2", "single": "one"},
        "body": {"hello": "world"},
    }


def test_vpclatticev2_dynamic_route_with_query_string():
    # GIVEN a VPC Lattice V2 event for a dynamic route, with the query string in path
    app = VPCLatticeV2Resolver()

    @app.get("/orders/<order_id>")
    def get_order(order_id: str):
        return {"order_id": order_id, "expand": app.current_event.query_string_parameters["expand"]}

    event = load_event("vpcLatticeV2Event.json")
    event["path"] = "/orders/42?expand=items"
    event["queryStringParameters"] = {"expand": ["items"]}

    # WHEN calling the event handler
    result = app(event, {})

    # THEN the path parameter does not include the query string
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"order_id": "42", "expand": "items"}


def test_vpclatticev2_resolve_async_with_query_string():
    # GIVEN an async handler for a VPC Lattice V2 event whose path carries the query string
    app = VPCLatticeV2Resolver()

    @app.post("/echo")
    async def echo():
        return {"single": app.current_event.query_string_parameters["single"]}

    # WHEN resolving the event asynchronously
    result = asyncio.run(app.resolve_async(load_event("vpcLatticeV2EventWithQueryString.json"), {}))

    # THEN the route matches the path without the query string
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"single": "one"}


def test_cors_preflight_body_is_empty_not_null():
    # GIVEN CORS is configured
    app = VPCLatticeV2Resolver(cors=CORSConfig())

    event = {"path": "/my/request", "method": "OPTIONS", "headers": {}}

    # WHEN calling the event handler
    result = app(event, {})

    # THEN there body should be empty strings
    assert result["body"] == ""


def test_vpclatticev2_url_no_matches():
    # GIVEN a VPC Lattice event
    app = VPCLatticeV2Resolver()

    @app.post("/no_match")
    def foo():
        raise RuntimeError()

    # WHEN calling the event handler
    result = app(load_event("vpcLatticeV2Event.json"), {})

    # THEN process event correctly
    # AND return 404 because the event doesn't match any known route
    assert result["statusCode"] == 404
