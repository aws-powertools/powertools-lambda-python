from __future__ import annotations

import json

from aws_lambda_powertools.event_handler import (
    Response,
    VPCLatticeResolver,
    content_types,
)
from aws_lambda_powertools.event_handler.api_gateway import CORSConfig
from aws_lambda_powertools.utilities.data_classes import VPCLatticeEvent
from tests.functional.utils import load_event


def test_vpclattice_event():
    # GIVEN a VPC Lattice event
    app = VPCLatticeResolver()

    @app.get("/testpath")
    def foo():
        assert isinstance(app.current_event, VPCLatticeEvent)
        assert app.lambda_context == {}
        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler
    result = app(load_event("vpcLatticeEvent.json"), {})

    # THEN process event correctly
    # AND set the current_event type as VPCLatticeEvent
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == content_types.TEXT_HTML
    assert result["body"] == "foo"


def test_vpclattice_event_path_trailing_slash(json_dump):
    # GIVEN a VPC Lattice event
    app = VPCLatticeResolver()

    @app.get("/testpath")
    def foo():
        assert isinstance(app.current_event, VPCLatticeEvent)
        assert app.lambda_context == {}
        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler using path with trailing "/"
    result = app(load_event("vpcLatticeEventPathTrailingSlash.json"), {})

    # THEN
    assert result["statusCode"] == 404
    assert result["headers"]["Content-Type"] == content_types.APPLICATION_JSON
    expected = {"statusCode": 404, "message": "Not found"}
    assert result["body"] == json_dump(expected)


def test_vpclattice_event_with_query_string():
    # GIVEN a VPC Lattice event whose raw_path carries the query string
    app = VPCLatticeResolver()

    @app.get("/testpath")
    def foo():
        return {"order_id": app.current_event.query_string_parameters["order-id"]}

    # WHEN calling the event handler
    result = app(load_event("vpcLatticeEventWithQueryString.json"), {})

    # THEN the route matches the path without the query string
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"order_id": "1"}


def test_vpclattice_dynamic_route_with_query_string():
    # GIVEN a VPC Lattice event for a dynamic route, with the query string in raw_path
    app = VPCLatticeResolver()

    @app.get("/orders/<order_id>")
    def get_order(order_id: str):
        return {"order_id": order_id, "expand": app.current_event.query_string_parameters["expand"]}

    event = load_event("vpcLatticeEvent.json")
    event["raw_path"] = "/orders/42?expand=items"
    event["query_string_parameters"] = {"expand": "items"}

    # WHEN calling the event handler
    result = app(event, {})

    # THEN the path parameter does not include the query string
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"order_id": "42", "expand": "items"}


def test_cors_preflight_body_is_empty_not_null():
    # GIVEN CORS is configured
    app = VPCLatticeResolver(cors=CORSConfig())

    event = {"raw_path": "/my/request", "method": "OPTIONS", "headers": {}}

    # WHEN calling the event handler
    result = app(event, {})

    # THEN there body should be empty strings
    assert result["body"] == ""


def test_vpclattice_url_no_matches():
    # GIVEN a VPC Lattice event
    app = VPCLatticeResolver()

    @app.post("/no_match")
    def foo():
        raise RuntimeError()

    # WHEN calling the event handler
    result = app(load_event("vpcLatticeEvent.json"), {})

    # THEN process event correctly
    # AND return 404 because the event doesn't match any known route
    assert result["statusCode"] == 404
