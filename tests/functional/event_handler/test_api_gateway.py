import base64
import json
import zlib
from decimal import Decimal
from pathlib import Path
from typing import Dict, Tuple

import pytest

from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, CORSConfig, ProxyEventType, Response
from aws_lambda_powertools.shared.json_encoder import Encoder
from aws_lambda_powertools.utilities.data_classes import ALBEvent, APIGatewayProxyEvent, APIGatewayProxyEventV2
from tests.functional.utils import load_event


def read_media(file_name: str) -> bytes:
    path = Path(str(Path(__file__).parent.parent.parent.parent) + "/docs/media/" + file_name)
    return path.read_bytes()


LOAD_GW_EVENT = load_event("apiGatewayProxyEvent.json")
TEXT_HTML = "text/html"
APPLICATION_JSON = "application/json"


def test_alb_event():
    # GIVEN a Application Load Balancer proxy type event
    app = ApiGatewayResolver(proxy_type=ProxyEventType.alb_event)

    @app.get("/lambda")
    def foo() -> Tuple[int, str, str]:
        assert isinstance(app.current_event, ALBEvent)
        assert app.lambda_context == {}
        return 200, TEXT_HTML, "foo"

    # WHEN calling the event handler
    result = app(load_event("albEvent.json"), {})

    # THEN process event correctly
    # AND set the current_event type as ALBEvent
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == TEXT_HTML
    assert result["body"] == "foo"


def test_api_gateway_v1():
    # GIVEN a Http API V1 proxy type event
    app = ApiGatewayResolver(proxy_type=ProxyEventType.http_api_v1)

    @app.get("/my/path")
    def get_lambda() -> Tuple[int, str, str]:
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        assert app.lambda_context == {}
        return 200, APPLICATION_JSON, json.dumps({"foo": "value"})

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == APPLICATION_JSON


def test_api_gateway():
    # GIVEN a Rest API Gateway proxy type event
    app = ApiGatewayResolver(proxy_type=ProxyEventType.api_gateway)

    @app.get("/my/path")
    def get_lambda() -> Tuple[int, str, str]:
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        return 200, TEXT_HTML, "foo"

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == TEXT_HTML
    assert result["body"] == "foo"


def test_api_gateway_v2():
    # GIVEN a Http API V2 proxy type event
    app = ApiGatewayResolver(proxy_type=ProxyEventType.http_api_v2)

    @app.post("/my/path")
    def my_path() -> Tuple[int, str, str]:
        assert isinstance(app.current_event, APIGatewayProxyEventV2)
        post_data = app.current_event.json_body
        return 200, "plain/text", post_data["username"]

    # WHEN calling the event handler
    result = app(load_event("apiGatewayProxyV2Event.json"), {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEventV2
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == "plain/text"
    assert result["body"] == "tom"


def test_include_rule_matching():
    # GIVEN
    app = ApiGatewayResolver()

    @app.get("/<name>/<my_id>")
    def get_lambda(my_id: str, name: str) -> Tuple[int, str, str]:
        assert name == "my"
        return 200, "plain/html", my_id

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN
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
    # GIVEN a function with cors=True
    # AND http method set to GET
    app = ApiGatewayResolver()

    @app.get("/my/path", cors=True)
    def with_cors() -> Tuple[int, str, str]:
        return 200, TEXT_HTML, "test"

    def handler(event, context):
        return app.resolve(event, context)

    # WHEN calling the event handler
    result = handler(LOAD_GW_EVENT, None)

    # THEN the headers should include cors headers
    assert "headers" in result
    headers = result["headers"]
    assert headers["Content-Type"] == TEXT_HTML
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert headers["Access-Control-Allow-Credentials"] == "true"
    # AND "Access-Control-Allow-Methods" is only included in the preflight cors headers
    assert "Access-Control-Allow-Methods" not in headers
    assert headers["Access-Control-Allow-Headers"] == ",".join(sorted(CORSConfig._REQUIRED_HEADERS))


def test_compress():
    # GIVEN a function that has compress=True
    # AND an event with a "Accept-Encoding" that include gzip
    app = ApiGatewayResolver()
    mock_event = {"path": "/my/request", "httpMethod": "GET", "headers": {"Accept-Encoding": "deflate, gzip"}}
    expected_value = '{"test": "value"}'

    @app.get("/my/request", compress=True)
    def with_compression() -> Tuple[int, str, str]:
        return 200, APPLICATION_JSON, expected_value

    def handler(event, context):
        return app.resolve(event, context)

    # WHEN calling the event handler
    result = handler(mock_event, None)

    # THEN then gzip the response and base64 encode as a string
    assert result["isBase64Encoded"] is True
    body = result["body"]
    assert isinstance(body, str)
    decompress = zlib.decompress(base64.b64decode(body), wbits=zlib.MAX_WBITS | 16).decode("UTF-8")
    assert decompress == expected_value
    headers = result["headers"]
    assert headers["Content-Encoding"] == "gzip"


def test_base64_encode():
    # GIVEN a function that returns bytes
    app = ApiGatewayResolver()
    mock_event = {"path": "/my/path", "httpMethod": "GET", "headers": {"Accept-Encoding": "deflate, gzip"}}

    @app.get("/my/path", compress=True)
    def read_image() -> Tuple[int, str, bytes]:
        return 200, "image/png", read_media("idempotent_sequence_exception.png")

    # WHEN calling the event handler
    result = app(mock_event, None)

    # THEN return the body and a base64 encoded string
    assert result["isBase64Encoded"] is True
    body = result["body"]
    assert isinstance(body, str)
    headers = result["headers"]
    assert headers["Content-Encoding"] == "gzip"


def test_compress_no_accept_encoding():
    # GIVEN a function with compress=True
    # AND the request has no "Accept-Encoding" set to include gzip
    app = ApiGatewayResolver()
    expected_value = "Foo"

    @app.get("/my/path", compress=True)
    def return_text() -> Tuple[int, str, str]:
        return 200, "text/plain", expected_value

    # WHEN calling the event handler
    result = app({"path": "/my/path", "httpMethod": "GET", "headers": {}}, None)

    # THEN don't perform any gzip compression
    assert result["isBase64Encoded"] is False
    assert result["body"] == expected_value


def test_cache_control_200():
    # GIVEN a function with cache_control set
    app = ApiGatewayResolver()

    @app.get("/success", cache_control="max-age=600")
    def with_cache_control() -> Tuple[int, str, str]:
        return 200, TEXT_HTML, "has 200 response"

    def handler(event, context):
        return app.resolve(event, context)

    # WHEN calling the event handler
    # AND the function returns a 200 status code
    result = handler({"path": "/success", "httpMethod": "GET"}, None)

    # THEN return the set Cache-Control
    headers = result["headers"]
    assert headers["Content-Type"] == TEXT_HTML
    assert headers["Cache-Control"] == "max-age=600"


def test_cache_control_non_200():
    # GIVEN a function with cache_control set
    app = ApiGatewayResolver()

    @app.delete("/fails", cache_control="max-age=600")
    def with_cache_control_has_500() -> Tuple[int, str, str]:
        return 503, TEXT_HTML, "has 503 response"

    def handler(event, context):
        return app.resolve(event, context)

    # WHEN calling the event handler
    # AND the function returns a 503 status code
    result = handler({"path": "/fails", "httpMethod": "DELETE"}, None)

    # THEN return a Cache-Control of "no-cache"
    headers = result["headers"]
    assert headers["Content-Type"] == TEXT_HTML
    assert headers["Cache-Control"] == "no-cache"


def test_rest_api():
    # GIVEN a function that returns a Dict
    app = ApiGatewayResolver(proxy_type=ProxyEventType.http_api_v1)
    expected_dict = {"foo": "value", "second": Decimal("100.01")}

    @app.get("/my/path")
    def rest_func() -> Dict:
        return expected_dict

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN automatically process this as a json rest api response
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == APPLICATION_JSON
    expected_str = json.dumps(expected_dict, separators=(",", ":"), indent=None, cls=Encoder)
    assert result["body"] == expected_str


def test_handling_response_type():
    # GIVEN a function that returns Response
    app = ApiGatewayResolver(proxy_type=ProxyEventType.http_api_v1)

    @app.get("/my/path")
    def rest_func() -> Response:
        return Response(
            status_code=404,
            content_type="used-if-not-set-in-header",
            body="Not found",
            headers={"Content-Type": "header-content-type-wins", "custom": "value"},
        )

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN the result can include some additional field control like overriding http headers
    assert result["statusCode"] == 404
    assert result["headers"]["Content-Type"] == "header-content-type-wins"
    assert result["headers"]["custom"] == "value"
    assert result["body"] == "Not found"


def test_preflight_cors():
    # GIVEN
    app = ApiGatewayResolver()
    preflight_event = {"path": "/cors", "httpMethod": "OPTIONS"}

    @app.get("/cors", cors=True)
    def get_with_cors():
        ...

    @app.post("/cors", cors=True)
    def post_with_cors():
        ...

    @app.delete("/cors")
    def delete_no_cors():
        ...

    def handler(event, context):
        return app.resolve(event, context)

    # WHEN calling the event handler
    # AND the httpMethod is OPTIONS
    result = handler(preflight_event, None)

    # THEN return the preflight response
    # AND No Content it returned
    assert result["statusCode"] == 204
    assert "body" not in result
    assert "isBase64Encoded" not in result
    # AND no Content-Type is set
    headers = result["headers"]
    assert "headers" in result
    assert "Content-Type" not in headers
    # AND set the access control headers
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert headers["Access-Control-Allow-Methods"] == "GET,OPTIONS,POST"
    assert headers["Access-Control-Allow-Credentials"] == "true"


def test_custom_cors_config():
    # GIVEN a custom cors configuration
    app = ApiGatewayResolver()
    event = {"path": "/cors", "httpMethod": "GET"}
    allow_header = ["foo2"]
    cors_config = CORSConfig(
        allow_origin="https://foo1",
        expose_headers=["foo1"],
        allow_headers=allow_header,
        max_age=100,
        allow_credentials=False,
    )

    @app.get("/cors", cors=cors_config)
    def get_with_cors():
        return {}

    # NOTE: Currently only the first configuration is used for the OPTIONS preflight
    @app.get("/another-one", cors=True)
    def another_one():
        return {}

    # WHEN calling the event handler
    result = app(event, None)

    # THEN return the custom cors headers
    assert "headers" in result
    headers = result["headers"]
    assert headers["Content-Type"] == APPLICATION_JSON
    assert headers["Access-Control-Allow-Origin"] == cors_config.allow_origin
    expected_allows_headers = ",".join(sorted(set(allow_header + cors_config._REQUIRED_HEADERS)))
    assert headers["Access-Control-Allow-Headers"] == expected_allows_headers
    assert headers["Access-Control-Expose-Headers"] == ",".join(cors_config.expose_headers)
    assert headers["Access-Control-Max-Age"] == str(cors_config.max_age)
    assert "Access-Control-Allow-Credentials" not in headers

    # AND custom cors was set on the app
    assert isinstance(app._cors, CORSConfig)
    assert app._cors is cors_config
    assert app._cors_methods == {"GET"}
