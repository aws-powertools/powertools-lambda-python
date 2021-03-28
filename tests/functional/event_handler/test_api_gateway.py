import json
import os

import pytest

from aws_lambda_powertools.utilities.data_classes import ALBEvent, APIGatewayProxyEvent, APIGatewayProxyEventV2
from aws_lambda_powertools.utilities.event_handler.api_gateway import ApiGatewayResolver, ProxyEventType
from aws_lambda_powertools.utilities.typing import LambdaContext


def load_event(file_name: str) -> dict:
    full_file_name = os.path.dirname(os.path.realpath(__file__)) + "/../../events/" + file_name
    with open(full_file_name) as fp:
        return json.load(fp)


def test_alb_event():
    app = ApiGatewayResolver(proxy_type=ProxyEventType.alb_event)

    @app.get("/lambda", include_event=True, include_context=True)
    def foo(event: ALBEvent, context: LambdaContext):
        assert isinstance(event, ALBEvent)
        assert context == {}
        return 200, "text/html", "foo"

    result = app(load_event("albEvent.json"), {})

    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == "text/html"
    assert result["body"] == "foo"


def test_api_gateway_v1():
    app = ApiGatewayResolver(proxy_type=ProxyEventType.http_api_v1)

    @app.get("/my/path", include_event=True, include_context=True)
    def get_lambda(event: APIGatewayProxyEvent, context: LambdaContext):
        assert isinstance(event, APIGatewayProxyEvent)
        assert context == {}
        return 200, "application/json", json.dumps({"foo": "value"})

    result = app(load_event("apiGatewayProxyEvent.json"), {})

    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == "application/json"


def test_include_rule_matching():
    app = ApiGatewayResolver()

    @app.get("/<name>/<my_id>")
    def get_lambda(my_id: str, name: str):
        assert name == "my"
        return 200, "plain/html", my_id

    result = app(load_event("apiGatewayProxyEvent.json"), {})

    assert result["statusCode"] == 200
    assert result["body"] == "path"


def test_include_event_false():
    app = ApiGatewayResolver()

    @app.get("/my/path")
    def get_lambda():
        return 200, "plain/html", "foo"

    result = app(load_event("apiGatewayProxyEvent.json"), {})

    assert result["statusCode"] == 200
    assert result["body"] == "foo"


def test_api_gateway_v2():
    app = ApiGatewayResolver(proxy_type=ProxyEventType.http_api_v2)

    @app.post("/my/path", include_event=True)
    def my_path(event: APIGatewayProxyEventV2):
        assert isinstance(event, APIGatewayProxyEventV2)
        post_data = json.loads(event.body or "{}")
        return 200, "plain/text", post_data["username"]

    result = app(load_event("apiGatewayProxyV2Event.json"), {})

    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == "plain/text"
    assert result["body"] == "tom"


def test_no_matches():
    app = ApiGatewayResolver()

    @app.get("/not_matching_get")
    def no_get_matching():
        raise RuntimeError()

    @app.put("/no_matching")
    def no_put_matching():
        raise RuntimeError()

    @app.delete("/no_matching")
    def no_delete_matching():
        raise RuntimeError()

    def handler(event, context):
        app.resolve(event, context)

    with pytest.raises(ValueError):
        handler(load_event("apiGatewayProxyEvent.json"), None)
