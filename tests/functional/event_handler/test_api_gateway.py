import base64
import json
import os
import zlib

import pytest

from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, ProxyEventType
from aws_lambda_powertools.utilities.data_classes import ALBEvent, APIGatewayProxyEvent, APIGatewayProxyEventV2


def load_event(file_name: str) -> dict:
    full_file_name = os.path.dirname(os.path.realpath(__file__)) + "/../../events/" + file_name
    with open(full_file_name) as fp:
        return json.load(fp)


def test_alb_event():
    app = ApiGatewayResolver(proxy_type=ProxyEventType.alb_event)

    @app.get("/lambda")
    def foo():
        assert isinstance(app.current_event, ALBEvent)
        assert app.lambda_context == {}
        return 200, "text/html", "foo"

    result = app(load_event("albEvent.json"), {})

    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == "text/html"
    assert result["body"] == "foo"


def test_api_gateway_v1():
    app = ApiGatewayResolver(proxy_type=ProxyEventType.http_api_v1)

    @app.get("/my/path")
    def get_lambda():
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        assert app.lambda_context == {}
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
    assert result["headers"]["Content-Type"] == "plain/html"
    assert result["body"] == "path"


def test_api_gateway():
    app = ApiGatewayResolver(proxy_type=ProxyEventType.api_gateway)

    @app.get("/my/path")
    def get_lambda():
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        return 200, "plain/html", "foo"

    result = app(load_event("apiGatewayProxyEvent.json"), {})

    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == "plain/html"
    assert result["body"] == "foo"


def test_api_gateway_v2():
    app = ApiGatewayResolver(proxy_type=ProxyEventType.http_api_v2)

    @app.post("/my/path")
    def my_path():
        assert isinstance(app.current_event, APIGatewayProxyEventV2)
        post_data = app.current_event.json_body
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


def test_cors():
    app = ApiGatewayResolver()

    @app.get("/my/path", cors=True)
    def with_cors():
        return 200, "text/html", "test"

    def handler(event, context):
        return app.resolve(event, context)

    result = handler(load_event("apiGatewayProxyEvent.json"), None)

    assert "headers" in result
    headers = result["headers"]
    assert headers["Content-Type"] == "text/html"
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert headers["Access-Control-Allow-Methods"] == "GET"
    assert headers["Access-Control-Allow-Credentials"] == "true"


def test_compress():
    mock_event = {"path": "/my/request", "httpMethod": "GET", "headers": {"Accept-Encoding": "deflate, gzip"}}
    expected_value = '{"test": "value"}'

    app = ApiGatewayResolver()

    @app.get("/my/request", compress=True)
    def with_compression():
        return 200, "application/json", expected_value

    def handler(event, context):
        return app.resolve(event, context)

    result = handler(mock_event, None)

    assert result["isBase64Encoded"] is True
    body = result["body"]
    assert isinstance(body, str)
    decompress = zlib.decompress(base64.b64decode(body), wbits=zlib.MAX_WBITS | 16).decode("UTF-8")
    assert decompress == expected_value


def test_cache_control_200():
    app = ApiGatewayResolver()

    @app.get("/success", cache_control="max-age=600")
    def with_cache_control():
        return 200, "text/html", "has 200 response"

    def handler(event, context):
        return app.resolve(event, context)

    result = handler({"path": "/success", "httpMethod": "GET"}, None)

    headers = result["headers"]
    assert headers["Cache-Control"] == "max-age=600"


def test_cache_control_non_200():
    app = ApiGatewayResolver()

    @app.delete("/fails", cache_control="max-age=600")
    def with_cache_control_has_500():
        return 503, "text/html", "has 503 response"

    def handler(event, context):
        return app.resolve(event, context)

    result = handler({"path": "/fails", "httpMethod": "DELETE"}, None)

    headers = result["headers"]
    assert headers["Cache-Control"] == "no-cache"
