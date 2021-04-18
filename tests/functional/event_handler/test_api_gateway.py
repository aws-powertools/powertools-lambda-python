import base64
import json
import zlib
from pathlib import Path

import pytest

from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, ProxyEventType
from aws_lambda_powertools.utilities.data_classes import ALBEvent, APIGatewayProxyEvent, APIGatewayProxyEventV2


def load_event(file_name: str) -> dict:
    path = Path(str(Path(__file__).parent.parent.parent) + "/events/" + file_name)
    return json.loads(path.read_text())


def read_media(file_name: str) -> bytes:
    path = Path(str(Path(__file__).parent.parent.parent.parent) + "/docs/media/" + file_name)
    return path.read_bytes()


LOAD_GW_EVENT = load_event("apiGatewayProxyEvent.json")
TEXT_HTML = "text/html"
APPLICATION_JSON = "application/json"


def test_alb_event():
    app = ApiGatewayResolver(proxy_type=ProxyEventType.alb_event)

    @app.get("/lambda")
    def foo():
        assert isinstance(app.current_event, ALBEvent)
        assert app.lambda_context == {}
        return 200, TEXT_HTML, "foo"

    result = app(load_event("albEvent.json"), {})

    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == TEXT_HTML
    assert result["body"] == "foo"


def test_api_gateway_v1():
    app = ApiGatewayResolver(proxy_type=ProxyEventType.http_api_v1)

    @app.get("/my/path")
    def get_lambda():
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        assert app.lambda_context == {}
        return 200, APPLICATION_JSON, json.dumps({"foo": "value"})

    result = app(LOAD_GW_EVENT, {})

    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == APPLICATION_JSON


def test_api_gateway():
    app = ApiGatewayResolver(proxy_type=ProxyEventType.api_gateway)

    @app.get("/my/path")
    def get_lambda():
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        return 200, TEXT_HTML, "foo"

    result = app(LOAD_GW_EVENT, {})

    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == TEXT_HTML
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


def test_include_rule_matching():
    app = ApiGatewayResolver()

    @app.get("/<name>/<my_id>")
    def get_lambda(my_id: str, name: str):
        assert name == "my"
        return 200, "plain/html", my_id

    result = app(LOAD_GW_EVENT, {})

    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == "plain/html"
    assert result["body"] == "path"


def test_no_matches():
    # GIVEN an event that does not match any of the given routes
    app = ApiGatewayResolver()

    @app.get("/not_matching_get")
    def get_func():
        raise RuntimeError()

    @app.post("/no_matching_post")
    def post_func():
        raise RuntimeError()

    @app.put("/no_matching_put")
    def put_func():
        raise RuntimeError()

    @app.delete("/no_matching_delete")
    def delete_func():
        raise RuntimeError()

    @app.patch("/no_matching_patch")
    def patch_func():
        raise RuntimeError()

    def handler(event, context):
        app.resolve(event, context)

    # Also check check the route configurations
    routes = app._routes
    assert len(routes) == 5
    for route in routes:
        if route.func == get_func:
            assert route.method == "GET"
        elif route.func == post_func:
            assert route.method == "POST"
        elif route.func == put_func:
            assert route.method == "PUT"
        elif route.func == delete_func:
            assert route.method == "DELETE"
        elif route.func == patch_func:
            assert route.method == "PATCH"

    # WHEN calling the handler
    # THEN raise a ValueError
    with pytest.raises(ValueError):
        handler(LOAD_GW_EVENT, None)


def test_cors():
    app = ApiGatewayResolver()

    @app.get("/my/path", cors=True)
    def with_cors():
        return 200, TEXT_HTML, "test"

    def handler(event, context):
        return app.resolve(event, context)

    result = handler(LOAD_GW_EVENT, None)

    assert "headers" in result
    headers = result["headers"]
    assert headers["Content-Type"] == TEXT_HTML
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert headers["Access-Control-Allow-Methods"] == "GET"
    assert headers["Access-Control-Allow-Credentials"] == "true"


def test_compress():
    mock_event = {"path": "/my/request", "httpMethod": "GET", "headers": {"Accept-Encoding": "deflate, gzip"}}
    expected_value = '{"test": "value"}'

    app = ApiGatewayResolver()

    @app.get("/my/request", compress=True)
    def with_compression():
        return 200, APPLICATION_JSON, expected_value

    def handler(event, context):
        return app.resolve(event, context)

    result = handler(mock_event, None)

    assert result["isBase64Encoded"] is True
    body = result["body"]
    assert isinstance(body, str)
    decompress = zlib.decompress(base64.b64decode(body), wbits=zlib.MAX_WBITS | 16).decode("UTF-8")
    assert decompress == expected_value
    headers = result["headers"]
    assert headers["Content-Encoding"] == "gzip"


def test_base64_encode():
    app = ApiGatewayResolver()

    @app.get("/my/path", compress=True)
    def read_image():
        return 200, "image/png", read_media("idempotent_sequence_exception.png")

    mock_event = {"path": "/my/path", "httpMethod": "GET", "headers": {"Accept-Encoding": "deflate, gzip"}}
    result = app(mock_event, None)

    assert result["isBase64Encoded"] is True
    body = result["body"]
    assert isinstance(body, str)
    headers = result["headers"]
    assert headers["Content-Encoding"] == "gzip"


def test_compress_no_accept_encoding():
    app = ApiGatewayResolver()
    expected_value = "Foo"

    @app.get("/my/path", compress=True)
    def return_text():
        return 200, "text/plain", expected_value

    result = app({"path": "/my/path", "httpMethod": "GET", "headers": {}}, None)

    assert result["isBase64Encoded"] is False
    assert result["body"] == expected_value


def test_cache_control_200():
    app = ApiGatewayResolver()

    @app.get("/success", cache_control="max-age=600")
    def with_cache_control():
        return 200, TEXT_HTML, "has 200 response"

    def handler(event, context):
        return app.resolve(event, context)

    result = handler({"path": "/success", "httpMethod": "GET"}, None)

    headers = result["headers"]
    assert headers["Content-Type"] == TEXT_HTML
    assert headers["Cache-Control"] == "max-age=600"


def test_cache_control_non_200():
    app = ApiGatewayResolver()

    @app.delete("/fails", cache_control="max-age=600")
    def with_cache_control_has_500():
        return 503, TEXT_HTML, "has 503 response"

    def handler(event, context):
        return app.resolve(event, context)

    result = handler({"path": "/fails", "httpMethod": "DELETE"}, None)

    headers = result["headers"]
    assert headers["Content-Type"] == TEXT_HTML
    assert headers["Cache-Control"] == "no-cache"


def test_rest_api():
    app = ApiGatewayResolver(proxy_type=ProxyEventType.http_api_v1)

    @app.get("/my/path")
    def rest_func():
        return {"foo": "value"}

    result = app(LOAD_GW_EVENT, {})

    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == APPLICATION_JSON
    assert result["body"] == json.dumps({"foo": "value"})
