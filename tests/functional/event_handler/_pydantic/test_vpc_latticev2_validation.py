from __future__ import annotations

import json
from typing import Annotated

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import VPCLatticeV2Resolver
from aws_lambda_powertools.event_handler.openapi.params import Body, Form
from tests.functional.utils import load_event


class EchoItem(BaseModel):
    hello: str


class EchoNumber(BaseModel):
    hello: int


def test_vpclatticev2_validation_json_body_with_list_content_type():
    # GIVEN a V2 resolver with validation and a route taking a JSON body
    app = VPCLatticeV2Resolver(enable_validation=True)

    @app.post("/echo")
    def echo(item: Annotated[EchoItem, Body()]):
        return item.model_dump()

    # WHEN resolving the event captured from a VPC Lattice V2 target group, where content-type is a list
    result = app(load_event("vpcLatticeV2EventWithQueryString.json"), {})

    # THEN the body is parsed and validated like in any other resolver
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"hello": "world"}


def test_vpclatticev2_validation_form_body_with_list_content_type():
    # GIVEN a V2 resolver with validation and a route taking a form field
    app = VPCLatticeV2Resolver(enable_validation=True)

    @app.post("/echo")
    def echo(name: Annotated[str, Form()]):
        return {"name": name}

    # WHEN resolving a V2 event with a URL-encoded form body and the content-type as a list
    event = load_event("vpcLatticeV2EventWithQueryString.json")
    event["headers"]["content-type"] = ["application/x-www-form-urlencoded"]
    event["body"] = "name=powertools"
    result = app(event, {})

    # THEN the form is parsed
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"name": "powertools"}


def test_vpclatticev2_validation_rejects_invalid_json_body_with_list_content_type():
    # GIVEN a V2 resolver with validation and a route taking a JSON body
    app = VPCLatticeV2Resolver(enable_validation=True)

    @app.post("/echo")
    def echo(item: Annotated[EchoNumber, Body()]):
        return item.model_dump()

    # WHEN the body does not match the model
    result = app(load_event("vpcLatticeV2EventWithQueryString.json"), {})

    # THEN validation answers 422 instead of crashing on the header
    assert result["statusCode"] == 422
