import base64
import json
import zlib
from copy import deepcopy
from decimal import Decimal
from enum import Enum
from json import JSONEncoder
from pathlib import Path
from typing import Dict

import pytest

from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import (
    ALBResolver,
    APIGatewayHttpResolver,
    ApiGatewayResolver,
    APIGatewayRestResolver,
    CORSConfig,
    ProxyEventType,
    Response,
    ResponseBuilder,
    Router,
)
from aws_lambda_powertools.event_handler.exceptions import (
    BadRequestError,
    InternalServerError,
    NotFoundError,
    ServiceError,
    UnauthorizedError,
)
from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.cookies import Cookie
from aws_lambda_powertools.shared.json_encoder import Encoder
from aws_lambda_powertools.utilities.data_classes import (
    ALBEvent,
    APIGatewayProxyEvent,
    APIGatewayProxyEventV2,
    event_source,
)
from tests.functional.utils import load_event


def read_media(file_name: str) -> bytes:
    path = Path(str(Path(__file__).parent.parent.parent.parent) + "/docs/media/" + file_name)
    return path.read_bytes()


LOAD_GW_EVENT = load_event("apiGatewayProxyEvent.json")
LOAD_GW_EVENT_TRAILING_SLASH = load_event("apiGatewayProxyEventPathTrailingSlash.json")


def test_alb_event():
    # GIVEN an Application Load Balancer proxy type event
    app = ALBResolver()

    @app.get("/lambda")
    def foo():
        assert isinstance(app.current_event, ALBEvent)
        assert app.lambda_context == {}
        assert app.current_event.request_context.elb_target_group_arn is not None
        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler
    result = app(load_event("albEvent.json"), {})

    # THEN process event correctly
    # AND set the current_event type as ALBEvent
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == content_types.TEXT_HTML
    assert result["body"] == "foo"


def test_alb_event_path_trailing_slash(json_dump):
    # GIVEN an Application Load Balancer proxy type event
    app = ALBResolver()

    @app.get("/lambda")
    def foo():
        assert isinstance(app.current_event, ALBEvent)
        assert app.lambda_context == {}
        assert app.current_event.request_context.elb_target_group_arn is not None
        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler using path with trailing "/"
    result = app(load_event("albEventPathTrailingSlash.json"), {})

    # THEN
    assert result["statusCode"] == 404
    assert result["headers"]["Content-Type"] == content_types.APPLICATION_JSON
    expected = {"statusCode": 404, "message": "Not found"}
    assert result["body"] == json_dump(expected)


def test_api_gateway_v1():
    # GIVEN a Http API V1 proxy type event
    app = APIGatewayRestResolver()

    @app.get("/my/path")
    def get_lambda() -> Response:
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        assert app.lambda_context == {}
        assert app.current_event.request_context.domain_name == "id.execute-api.us-east-1.amazonaws.com"
        return Response(200, content_types.APPLICATION_JSON, json.dumps({"foo": "value"}))

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]


def test_api_gateway_v1_path_trailing_slash():
    # GIVEN a Http API V1 proxy type event
    app = APIGatewayRestResolver()

    @app.get("/my/path")
    def get_lambda() -> Response:
        return Response(200, content_types.APPLICATION_JSON, json.dumps({"foo": "value"}))

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT_TRAILING_SLASH, {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]


def test_api_gateway_v1_cookies():
    # GIVEN a Http API V1 proxy type event
    app = APIGatewayRestResolver()
    cookie = Cookie(name="CookieMonster", value="MonsterCookie")

    @app.get("/my/path")
    def get_lambda() -> Response:
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        return Response(200, content_types.TEXT_PLAIN, "Hello world", cookies=[cookie])

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Set-Cookie"] == ["CookieMonster=MonsterCookie; Secure"]


def test_api_gateway():
    # GIVEN a Rest API Gateway proxy type event
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)

    @app.get("/my/path")
    def get_lambda() -> Response:
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.TEXT_HTML]
    assert result["body"] == "foo"


def test_api_gateway_event_path_trailing_slash(json_dump):
    # GIVEN a Rest API Gateway proxy type event
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)

    @app.get("/my/path")
    def get_lambda() -> Response:
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT_TRAILING_SLASH, {})
    # THEN
    assert result["statusCode"] == 404
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    expected = {"statusCode": 404, "message": "Not found"}
    assert result["body"] == json_dump(expected)


def test_api_gateway_v2():
    # GIVEN a Http API V2 proxy type event
    app = APIGatewayHttpResolver()

    @app.post("/my/path")
    def my_path() -> Response:
        assert isinstance(app.current_event, APIGatewayProxyEventV2)
        post_data = app.current_event.json_body
        assert app.current_event.cookies[0] == "cookie1"
        return Response(200, content_types.TEXT_PLAIN, post_data["username"])

    # WHEN calling the event handler
    result = app(load_event("apiGatewayProxyV2Event.json"), {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEventV2
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == content_types.TEXT_PLAIN
    assert "Cookies" not in result["headers"]
    assert result["body"] == "tom"


def test_api_gateway_v2_http_path_trailing_slash(json_dump):
    # GIVEN a Http API V2 proxy type event
    app = APIGatewayHttpResolver()

    @app.post("/my/path")
    def my_path() -> Response:
        post_data = app.current_event.json_body
        return Response(200, content_types.TEXT_PLAIN, post_data["username"])

    # WHEN calling the event handler
    result = app(load_event("apiGatewayProxyV2EventPathTrailingSlash.json"), {})

    # THEN expect a 404 response
    assert result["statusCode"] == 404
    assert result["headers"]["Content-Type"] == content_types.APPLICATION_JSON
    expected = {"statusCode": 404, "message": "Not found"}
    assert result["body"] == json_dump(expected)


def test_api_gateway_v2_cookies():
    # GIVEN a Http API V2 proxy type event
    app = APIGatewayHttpResolver()
    cookie = Cookie(name="CookieMonster", value="MonsterCookie")

    @app.post("/my/path")
    def my_path() -> Response:
        assert isinstance(app.current_event, APIGatewayProxyEventV2)
        return Response(200, content_types.TEXT_PLAIN, "Hello world", cookies=[cookie])

    # WHEN calling the event handler
    result = app(load_event("apiGatewayProxyV2Event.json"), {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEventV2
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == content_types.TEXT_PLAIN
    assert result["cookies"] == ["CookieMonster=MonsterCookie; Secure"]


def test_include_rule_matching():
    # GIVEN
    app = ApiGatewayResolver()

    @app.get("/<name>/<my_id>")
    def get_lambda(my_id: str, name: str) -> Response:
        assert name == "my"
        return Response(200, content_types.TEXT_HTML, my_id)

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.TEXT_HTML]
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
        return app.resolve(event, context)

    # Also check the route configurations
    routes = app._static_routes
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
    # THEN return a 404
    result = handler(LOAD_GW_EVENT, None)
    assert result["statusCode"] == 404
    # AND cors headers are not returned
    assert "Access-Control-Allow-Origin" not in result["multiValueHeaders"]


def test_cors():
    # GIVEN a function with cors=True
    # AND http method set to GET
    app = ApiGatewayResolver()

    @app.get("/my/path", cors=True)
    def with_cors() -> Response:
        return Response(200, content_types.TEXT_HTML, "test")

    @app.get("/without-cors")
    def without_cors() -> Response:
        return Response(200, content_types.TEXT_HTML, "test")

    def handler(event, context):
        return app.resolve(event, context)

    # WHEN calling the event handler
    result = handler(LOAD_GW_EVENT, None)

    # THEN the headers should include cors headers
    assert "multiValueHeaders" in result
    headers = result["multiValueHeaders"]
    assert headers["Content-Type"] == [content_types.TEXT_HTML]
    assert headers["Access-Control-Allow-Origin"] == ["https://aws.amazon.com"]
    assert "Access-Control-Allow-Credentials" not in headers
    assert headers["Access-Control-Allow-Headers"] == [",".join(sorted(CORSConfig._REQUIRED_HEADERS))]

    # THEN for routes without cors flag return no cors headers
    mock_event = {"path": "/my/request", "httpMethod": "GET"}
    result = handler(mock_event, None)
    assert "Access-Control-Allow-Origin" not in result["multiValueHeaders"]


def test_cors_preflight_body_is_empty_not_null():
    # GIVEN CORS is configured
    app = ALBResolver(cors=CORSConfig())

    event = {"path": "/my/request", "httpMethod": "OPTIONS"}

    # WHEN calling the event handler
    result = app(event, {})

    # THEN there body should be empty strings
    assert result["body"] == ""


def test_override_route_compress_parameter():
    # GIVEN a function that has compress=True
    # AND an event with a "Accept-Encoding" that include gzip
    # AND the Response object with compress=False
    app = ApiGatewayResolver()
    mock_event = {"path": "/my/request", "httpMethod": "GET", "headers": {"Accept-Encoding": "deflate, gzip"}}
    expected_value = '{"test": "value"}'

    @app.get("/my/request", compress=True)
    def with_compression() -> Response:
        return Response(200, content_types.APPLICATION_JSON, expected_value, compress=False)

    def handler(event, context):
        return app.resolve(event, context)

    # WHEN calling the event handler
    result = handler(mock_event, None)

    # THEN then the response is not compressed
    assert result["isBase64Encoded"] is False
    assert result["body"] == expected_value
    assert result["multiValueHeaders"].get("Content-Encoding") is None


def test_response_with_compress_enabled():
    # GIVEN a function
    # AND an event with a "Accept-Encoding" that include gzip
    # AND the Response object with compress=True
    app = ApiGatewayResolver()
    mock_event = {"path": "/my/request", "httpMethod": "GET", "headers": {"Accept-Encoding": "deflate, gzip"}}
    expected_value = '{"test": "value"}'

    @app.get("/my/request")
    def route_without_compression() -> Response:
        return Response(200, content_types.APPLICATION_JSON, expected_value, compress=True)

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
    headers = result["multiValueHeaders"]
    assert headers["Content-Encoding"] == ["gzip"]


def test_compress():
    # GIVEN a function that has compress=True
    # AND an event with a "Accept-Encoding" that include gzip
    app = ApiGatewayResolver()
    mock_event = {"path": "/my/request", "httpMethod": "GET", "headers": {"Accept-Encoding": "deflate, gzip"}}
    expected_value = '{"test": "value"}'

    @app.get("/my/request", compress=True)
    def with_compression() -> Response:
        return Response(200, content_types.APPLICATION_JSON, expected_value)

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
    headers = result["multiValueHeaders"]
    assert headers["Content-Encoding"] == ["gzip"]


def test_base64_encode():
    # GIVEN a function that returns bytes
    app = ApiGatewayResolver()
    mock_event = {"path": "/my/path", "httpMethod": "GET", "headers": {"Accept-Encoding": "deflate, gzip"}}

    @app.get("/my/path", compress=True)
    def read_image() -> Response:
        return Response(200, "image/png", read_media("tracer_utility_showcase.png"))

    # WHEN calling the event handler
    result = app(mock_event, None)

    # THEN return the body and a base64 encoded string
    assert result["isBase64Encoded"] is True
    body = result["body"]
    assert isinstance(body, str)
    headers = result["multiValueHeaders"]
    assert headers["Content-Encoding"] == ["gzip"]


def test_compress_no_accept_encoding():
    # GIVEN a function with compress=True
    # AND the request has no "Accept-Encoding" set to include gzip
    app = ApiGatewayResolver()
    expected_value = "Foo"

    @app.get("/my/path", compress=True)
    def return_text() -> Response:
        return Response(200, content_types.TEXT_PLAIN, expected_value)

    # WHEN calling the event handler
    result = app({"path": "/my/path", "httpMethod": "GET", "headers": {}}, None)

    # THEN don't perform any gzip compression
    assert result["isBase64Encoded"] is False
    assert result["body"] == expected_value


def test_compress_no_accept_encoding_null_headers():
    # GIVEN a function with compress=True
    # AND the request has no headers
    app = ApiGatewayResolver()
    expected_value = "Foo"

    @app.get("/my/path", compress=True)
    def return_text() -> Response:
        return Response(200, content_types.TEXT_PLAIN, expected_value)

    # WHEN calling the event handler
    result = app({"path": "/my/path", "httpMethod": "GET", "headers": None}, None)

    # THEN don't perform any gzip compression
    assert result["isBase64Encoded"] is False
    assert result["body"] == expected_value


def test_cache_control_200():
    # GIVEN a function with cache_control set
    app = ApiGatewayResolver()

    @app.get("/success", cache_control="max-age=600")
    def with_cache_control() -> Response:
        return Response(200, content_types.TEXT_HTML, "has 200 response")

    def handler(event, context):
        return app.resolve(event, context)

    # WHEN calling the event handler
    # AND the function returns a 200 status code
    result = handler({"path": "/success", "httpMethod": "GET"}, None)

    # THEN return the set Cache-Control
    headers = result["multiValueHeaders"]
    assert headers["Content-Type"] == [content_types.TEXT_HTML]
    assert headers["Cache-Control"] == ["max-age=600"]


def test_cache_control_non_200():
    # GIVEN a function with cache_control set
    app = ApiGatewayResolver()

    @app.delete("/fails", cache_control="max-age=600")
    def with_cache_control_has_500() -> Response:
        return Response(503, content_types.TEXT_HTML, "has 503 response")

    def handler(event, context):
        return app.resolve(event, context)

    # WHEN calling the event handler
    # AND the function returns a 503 status code
    result = handler({"path": "/fails", "httpMethod": "DELETE"}, None)

    # THEN return a Cache-Control of "no-cache"
    headers = result["multiValueHeaders"]
    assert headers["Content-Type"] == [content_types.TEXT_HTML]
    assert headers["Cache-Control"] == ["no-cache"]


def test_rest_api():
    # GIVEN a function that returns a Dict
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)
    expected_dict = {"foo": "value", "second": Decimal("100.01")}

    @app.get("/my/path")
    def rest_func() -> Dict:
        return expected_dict

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN automatically process this as a json rest api response
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    expected_str = json.dumps(expected_dict, separators=(",", ":"), indent=None, cls=Encoder)
    assert result["body"] == expected_str


def test_handling_response_type():
    # GIVEN a function that returns Response
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)

    @app.get("/my/path")
    def rest_func() -> Response:
        return Response(
            status_code=404,
            content_type="used-if-not-set-in-header",
            body="Not found",
            headers={"Content-Type": ["header-content-type-wins"], "custom": ["value"]},
        )

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN the result can include some additional field control like overriding http headers
    assert result["statusCode"] == 404
    assert result["multiValueHeaders"]["Content-Type"] == ["header-content-type-wins"]
    assert result["multiValueHeaders"]["custom"] == ["value"]
    assert result["body"] == "Not found"


def test_cors_multi_origin():
    # GIVEN a custom cors configuration with multiple origins
    cors_config = CORSConfig(allow_origin="https://origin1", extra_origins=["https://origin2", "https://origin3"])
    app = ApiGatewayResolver(cors=cors_config)

    @app.get("/cors")
    def get_with_cors():
        return {}

    # WHEN calling the event handler with the correct Origin
    event = {"path": "/cors", "httpMethod": "GET", "headers": {"Origin": "https://origin3"}}
    result = app(event, None)

    # THEN routes by default return the custom cors headers
    headers = result["multiValueHeaders"]
    assert headers["Content-Type"] == [content_types.APPLICATION_JSON]
    assert headers["Access-Control-Allow-Origin"] == ["https://origin3"]

    # WHEN calling the event handler with the wrong origin
    event = {"path": "/cors", "httpMethod": "GET", "headers": {"Origin": "https://wrong.origin"}}
    result = app(event, None)

    # THEN routes by default return the custom cors headers
    headers = result["multiValueHeaders"]
    assert headers["Content-Type"] == [content_types.APPLICATION_JSON]
    assert "Access-Control-Allow-Origin" not in headers


def test_custom_cors_config():
    # GIVEN a custom cors configuration
    allow_header = ["foo2"]
    cors_config = CORSConfig(
        allow_origin="https://foo1",
        expose_headers=["foo1"],
        allow_headers=allow_header,
        max_age=100,
        allow_credentials=True,
    )
    app = ApiGatewayResolver(cors=cors_config)
    event = {"path": "/cors", "httpMethod": "GET", "headers": {"Origin": "https://foo1"}}

    @app.get("/cors")
    def get_with_cors():
        return {}

    @app.get("/another-one", cors=False)
    def another_one():
        return {}

    # WHEN calling the event handler
    result = app(event, None)

    # THEN routes by default return the custom cors headers
    assert "multiValueHeaders" in result
    headers = result["multiValueHeaders"]
    assert headers["Content-Type"] == [content_types.APPLICATION_JSON]
    assert headers["Access-Control-Allow-Origin"] == ["https://foo1"]
    expected_allows_headers = [",".join(sorted(set(allow_header + cors_config._REQUIRED_HEADERS)))]
    assert headers["Access-Control-Allow-Headers"] == expected_allows_headers
    assert headers["Access-Control-Expose-Headers"] == [",".join(cors_config.expose_headers)]
    assert headers["Access-Control-Max-Age"] == [str(cors_config.max_age)]
    assert "Access-Control-Allow-Credentials" in headers
    assert headers["Access-Control-Allow-Credentials"] == ["true"]

    # AND custom cors was set on the app
    assert isinstance(app._cors, CORSConfig)
    assert app._cors is cors_config

    # AND routes without cors don't include "Access-Control" headers
    event = {"path": "/another-one", "httpMethod": "GET"}
    result = app(event, None)
    headers = result["multiValueHeaders"]
    assert "Access-Control-Allow-Origin" not in headers


def test_no_content_response():
    # GIVEN a response with no content-type or body
    response = Response(status_code=204, content_type=None, body=None, headers=None)
    response_builder = ResponseBuilder(response)

    # WHEN calling to_dict
    result = response_builder.build(APIGatewayProxyEvent(LOAD_GW_EVENT))

    # THEN return an None body and no Content-Type header
    assert result["statusCode"] == response.status_code
    assert result["body"] is None
    headers = result["multiValueHeaders"]
    assert "Content-Type" not in headers


def test_no_matches_with_cors():
    # GIVEN an event that does not match any of the given routes
    # AND cors enabled
    app = ApiGatewayResolver(cors=CORSConfig())

    # WHEN calling the handler
    result = app({"path": "/another-one", "httpMethod": "GET"}, None)

    # THEN return a 404
    # AND cors headers are NOT returned (because no Origin header was passed in)
    assert result["statusCode"] == 404
    assert "Access-Control-Allow-Origin" not in result["multiValueHeaders"]
    assert "Not found" in result["body"]


def test_cors_preflight():
    # GIVEN an event for an OPTIONS call that does not match any of the given routes
    # AND cors is enabled
    app = ApiGatewayResolver(cors=CORSConfig())

    @app.get("/foo")
    def foo_cors():
        ...

    @app.route(method="delete", rule="/foo")
    def foo_delete_cors():
        ...

    @app.post("/foo", cors=False)
    def post_no_cors():
        ...

    # WHEN calling the handler
    result = app({"path": "/foo", "httpMethod": "OPTIONS", "headers": {"Origin": "http://example.org"}}, None)

    # THEN return no content
    # AND include Access-Control-Allow-Methods of the cors methods used
    assert result["statusCode"] == 204
    assert result["body"] == ""
    headers = result["multiValueHeaders"]
    assert "Content-Type" not in headers
    assert "Access-Control-Allow-Origin" in result["multiValueHeaders"]
    assert headers["Access-Control-Allow-Methods"] == [",".join(sorted(["DELETE", "GET", "OPTIONS"]))]


def test_custom_preflight_response():
    # GIVEN cors is enabled
    # AND we have a custom preflight method
    # AND the request matches this custom preflight route
    app = ApiGatewayResolver(cors=CORSConfig())

    @app.route(method="OPTIONS", rule="/some-call", cors=True)
    def custom_preflight():
        return Response(
            status_code=200,
            content_type=content_types.TEXT_HTML,
            body="Foo",
            headers={"Access-Control-Allow-Methods": ["CUSTOM"]},
        )

    @app.route(method="CUSTOM", rule="/some-call", cors=True)
    def custom_method():
        ...

    # AND the request includes an origin
    headers = {"Origin": "https://example.org"}

    # WHEN calling the handler
    result = app({"path": "/some-call", "httpMethod": "OPTIONS", "headers": headers}, None)

    # THEN return the custom preflight response
    assert result["statusCode"] == 200
    assert result["body"] == "Foo"
    headers = result["multiValueHeaders"]
    assert headers["Content-Type"] == [content_types.TEXT_HTML]
    assert "Access-Control-Allow-Origin" in result["multiValueHeaders"]
    assert headers["Access-Control-Allow-Methods"] == ["CUSTOM"]


def test_service_error_responses(json_dump):
    # SCENARIO handling different kind of service errors being raised
    app = ApiGatewayResolver(cors=CORSConfig())

    # GIVEN an BadRequestError
    @app.get(rule="/bad-request-error", cors=False)
    def bad_request_error():
        raise BadRequestError("Missing required parameter")

    # WHEN calling the handler
    # AND path is /bad-request-error
    result = app({"path": "/bad-request-error", "httpMethod": "GET"}, None)
    # THEN return the bad request error response
    # AND status code equals 400
    assert result["statusCode"] == 400
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    expected = {"statusCode": 400, "message": "Missing required parameter"}
    assert result["body"] == json_dump(expected)

    # GIVEN an UnauthorizedError
    @app.get(rule="/unauthorized-error", cors=False)
    def unauthorized_error():
        raise UnauthorizedError("Unauthorized")

    # WHEN calling the handler
    # AND path is /unauthorized-error
    result = app({"path": "/unauthorized-error", "httpMethod": "GET"}, None)
    # THEN return the unauthorized error response
    # AND status code equals 401
    assert result["statusCode"] == 401
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    expected = {"statusCode": 401, "message": "Unauthorized"}
    assert result["body"] == json_dump(expected)

    # GIVEN an NotFoundError
    @app.get(rule="/not-found-error", cors=False)
    def not_found_error():
        raise NotFoundError

    # WHEN calling the handler
    # AND path is /not-found-error
    result = app({"path": "/not-found-error", "httpMethod": "GET"}, None)
    # THEN return the not found error response
    # AND status code equals 404
    assert result["statusCode"] == 404
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    expected = {"statusCode": 404, "message": "Not found"}
    assert result["body"] == json_dump(expected)

    # GIVEN an InternalServerError
    @app.get(rule="/internal-server-error", cors=False)
    def internal_server_error():
        raise InternalServerError("Internal server error")

    # WHEN calling the handler
    # AND path is /internal-server-error
    result = app({"path": "/internal-server-error", "httpMethod": "GET"}, None)
    # THEN return the internal server error response
    # AND status code equals 500
    assert result["statusCode"] == 500
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    expected = {"statusCode": 500, "message": "Internal server error"}
    assert result["body"] == json_dump(expected)

    # GIVEN an ServiceError with a custom status code
    @app.get(rule="/service-error", cors=True)
    def service_error():
        raise ServiceError(502, "Something went wrong!")

    # WHEN calling the handler
    # AND path is /service-error
    result = app({"path": "/service-error", "httpMethod": "GET"}, None)
    # THEN return the service error response
    # AND status code equals 502
    assert result["statusCode"] == 502
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    # Because no Origin was passed in, there is not Allow-Origin on the output
    assert "Access-Control-Allow-Origin" not in result["multiValueHeaders"]
    expected = {"statusCode": 502, "message": "Something went wrong!"}
    assert result["body"] == json_dump(expected)


def test_debug_unhandled_exceptions_debug_on():
    # GIVEN debug is enabled
    # AND an unhandled exception is raised
    app = ApiGatewayResolver(debug=True)
    assert app._debug

    @app.get("/raises-error")
    def raises_error():
        raise RuntimeError("Foo")

    # WHEN calling the handler
    result = app({"path": "/raises-error", "httpMethod": "GET"}, None)

    # THEN return a 500
    # AND Content-Type is set to text/plain
    # AND include the exception traceback in the response
    assert result["statusCode"] == 500
    assert "Traceback (most recent call last)" in result["body"]
    headers = result["multiValueHeaders"]
    assert headers["Content-Type"] == [content_types.TEXT_PLAIN]


def test_debug_unhandled_exceptions_debug_off():
    # GIVEN debug is disabled
    # AND an unhandled exception is raised
    app = ApiGatewayResolver(debug=False)
    assert not app._debug

    @app.get("/raises-error")
    def raises_error():
        raise RuntimeError("Foo")

    # WHEN calling the handler
    # THEN raise the original exception
    with pytest.raises(RuntimeError) as e:
        app({"path": "/raises-error", "httpMethod": "GET"}, None)

    # AND include the original error
    assert e.value.args == ("Foo",)


def test_powertools_dev_sets_debug_mode(monkeypatch):
    # GIVEN a debug mode environment variable is set
    monkeypatch.setenv(constants.POWERTOOLS_DEV_ENV, "true")
    app = ApiGatewayResolver()

    # WHEN calling app._debug
    # THEN the debug mode is enabled
    assert app._debug


def test_debug_json_formatting(json_dump):
    # GIVEN debug is True
    app = ApiGatewayResolver(debug=True)
    response = {"message": "Foo"}

    @app.get("/foo")
    def foo():
        return response

    # WHEN calling the handler
    result = app({"path": "/foo", "httpMethod": "GET"}, None)

    # THEN return a pretty print json in the body
    assert result["body"] == json_dump(response)


def test_debug_print_event(capsys):
    # GIVE debug is True
    app = ApiGatewayResolver(debug=True)

    # WHEN calling resolve
    event = {"path": "/foo", "httpMethod": "GET"}
    app(event, None)

    # THEN print the event
    out, err = capsys.readouterr()
    assert "\n" in out
    assert json.loads(out) == event


def test_similar_dynamic_routes():
    # GIVEN
    app = ApiGatewayResolver()
    event = deepcopy(LOAD_GW_EVENT)

    # WHEN
    # r'^/accounts/(?P<account_id>\\w+\\b)$' # noqa: ERA001
    @app.get("/accounts/<account_id>")
    def get_account(account_id: str):
        assert account_id == "single_account"

    # r'^/accounts/(?P<account_id>\\w+\\b)/source_networks$' # noqa: ERA001
    @app.get("/accounts/<account_id>/source_networks")
    def get_account_networks(account_id: str):
        assert account_id == "nested_account"

    # r'^/accounts/(?P<account_id>\\w+\\b)/source_networks/(?P<network_id>\\w+\\b)$' # noqa: ERA001
    @app.get("/accounts/<account_id>/source_networks/<network_id>")
    def get_network_account(account_id: str, network_id: str):
        assert account_id == "nested_account"
        assert network_id == "network"

    # THEN
    event["resource"] = "/accounts/{account_id}"
    event["path"] = "/accounts/single_account"
    app.resolve(event, None)

    event["resource"] = "/accounts/{account_id}/source_networks"
    event["path"] = "/accounts/nested_account/source_networks"
    app.resolve(event, None)

    event["resource"] = "/accounts/{account_id}/source_networks/{network_id}"
    event["path"] = "/accounts/nested_account/source_networks/network"
    app.resolve(event, {})


def test_similar_dynamic_routes_with_whitespaces():
    # GIVEN
    app = ApiGatewayResolver()
    event = deepcopy(LOAD_GW_EVENT)

    # WHEN
    # r'^/accounts/(?P<account_id>\\w+\\b)$' # noqa: ERA001
    @app.get("/accounts/<account_id>")
    def get_account(account_id: str):
        assert account_id == "single account"

    # r'^/accounts/(?P<account_id>\\w+\\b)/source_networks$' # noqa: ERA001
    @app.get("/accounts/<account_id>/source_networks")
    def get_account_networks(account_id: str):
        assert account_id == "nested account"

    # r'^/accounts/(?P<account_id>\\w+\\b)/source_networks/(?P<network_id>\\w+\\b)$' # noqa: ERA001
    @app.get("/accounts/<account_id>/source_networks/<network_id>")
    def get_network_account(account_id: str, network_id: str):
        assert account_id == "nested account"
        assert network_id == "network 123"

    # THEN
    event["resource"] = "/accounts/{account_id}"
    event["path"] = "/accounts/single account"
    assert app.resolve(event, {})["statusCode"] == 200

    event["resource"] = "/accounts/{account_id}/source_networks"
    event["path"] = "/accounts/nested account/source_networks"
    assert app.resolve(event, {})["statusCode"] == 200

    event["resource"] = "/accounts/{account_id}/source_networks/{network_id}"
    event["path"] = "/accounts/nested account/source_networks/network 123"
    assert app.resolve(event, {})["statusCode"] == 200


@pytest.mark.parametrize(
    "req",
    [
        pytest.param(123456789, id="num"),
        pytest.param("user@example.com", id="email"),
        pytest.param("-._~'!*:@,;()=", id="safe-rfc3986"),
        pytest.param("%<>[]{}|^", id="unsafe-rfc3986"),
    ],
)
def test_non_word_chars_route(req):
    # GIVEN
    app = ApiGatewayResolver()
    event = deepcopy(LOAD_GW_EVENT)

    # WHEN
    @app.get("/accounts/<account_id>")
    def get_account(account_id: str):
        assert account_id == f"{req}"

    # THEN
    event["resource"] = "/accounts/{account_id}"
    event["path"] = f"/accounts/{req}"

    ret = app.resolve(event, None)
    assert ret["statusCode"] == 200


def test_custom_serializer():
    # GIVEN a custom serializer to handle enums and sets
    class CustomEncoder(JSONEncoder):
        def default(self, data):
            if isinstance(data, Enum):
                return data.value
            try:
                iterable = iter(data)
            except TypeError:
                pass
            else:
                return sorted(iterable)
            return JSONEncoder.default(self, data)

    def custom_serializer(data) -> str:
        return json.dumps(data, cls=CustomEncoder)

    app = ApiGatewayResolver(serializer=custom_serializer)

    class Color(Enum):
        RED = 1
        BLUE = 2

    @app.get("/colors")
    def get_color() -> Dict:
        return {
            "color": Color.RED,
            "variations": {"light", "dark"},
        }

    # WHEN calling handler
    response = app({"httpMethod": "GET", "path": "/colors"}, None)

    # THEN then use the custom serializer
    body = response["body"]
    expected = '{"color": 1, "variations": ["dark", "light"]}'
    assert expected == body


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/pay/foo", id="path matched pay prefix"),
        pytest.param("/payment/foo", id="path matched payment prefix"),
        pytest.param("/foo", id="path does not start with any of the prefixes"),
    ],
)
def test_remove_prefix(path: str):
    # GIVEN events paths `/pay/foo`, `/payment/foo` or `/foo`
    # AND a configured strip_prefixes of `/pay` and `/payment`
    app = ApiGatewayResolver(strip_prefixes=["/pay", "/payment"])

    @app.get("/pay/foo")
    def pay_foo():
        raise ValueError("should not be matching")

    @app.get("/foo")
    def foo():
        ...

    # WHEN calling handler
    response = app({"httpMethod": "GET", "path": path}, None)

    # THEN a route for `/foo` should be found
    assert response["statusCode"] == 200


@pytest.mark.parametrize(
    "prefix",
    [
        pytest.param("/foo", id="String are not supported"),
        pytest.param({"/foo"}, id="Sets are not supported"),
        pytest.param({"foo": "/foo"}, id="Dicts are not supported"),
        pytest.param(tuple("/foo"), id="Tuples are not supported"),
        pytest.param([None, 1, "", False], id="List of invalid values"),
    ],
)
def test_ignore_invalid(prefix):
    # GIVEN an invalid prefix
    app = ApiGatewayResolver(strip_prefixes=prefix)

    @app.get("/foo/status")
    def foo():
        ...

    # WHEN calling handler
    response = app({"httpMethod": "GET", "path": "/foo/status"}, None)

    # THEN a route for `/foo/status` should be found
    # so no prefix was stripped from the request path
    assert response["statusCode"] == 200


def test_api_gateway_v2_raw_path():
    # GIVEN a Http API V2 proxy type event
    # AND a custom stage name "dev" and raw path "/dev/foo"
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEventV2)
    event = {"rawPath": "/dev/foo", "requestContext": {"http": {"method": "GET"}, "stage": "dev"}}

    @app.get("/foo")
    def foo():
        return {}

    # WHEN calling the event handler
    # WITH a route "/foo"
    result = app(event, {})

    # THEN process event correctly
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == content_types.APPLICATION_JSON


def test_api_gateway_request_path_equals_strip_prefix():
    # GIVEN a strip_prefix matches the request path
    app = ApiGatewayResolver(strip_prefixes=["/foo"])
    event = {"httpMethod": "GET", "path": "/foo"}

    @app.get("/")
    def base():
        return {}

    # WHEN calling the event handler
    # WITH a route "/"
    result = app(event, {})

    # THEN process event correctly
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]


def test_api_gateway_app_router():
    # GIVEN a Router with registered routes
    app = ApiGatewayResolver()
    router = Router()

    @router.get("/my/path")
    def foo():
        return {}

    app.include_router(router)
    # WHEN calling the event handler after applying routes from router object
    result = app(LOAD_GW_EVENT, {})

    # THEN process event correctly
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]


def test_api_gateway_app_router_with_params():
    # GIVEN a Router with registered routes
    app = ApiGatewayResolver()
    router = Router()
    req = "foo"
    event = deepcopy(LOAD_GW_EVENT)
    event["resource"] = "/accounts/{account_id}"
    event["path"] = f"/accounts/{req}"
    lambda_context = {}

    @router.route(rule="/accounts/<account_id>", method=["GET", "POST"])
    def foo(account_id):
        assert router.current_event.raw_event == event
        assert router.lambda_context == lambda_context
        assert account_id == f"{req}"
        return {}

    app.include_router(router)
    # WHEN calling the event handler after applying routes from router object
    result = app(event, lambda_context)

    # THEN process event correctly
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]


def test_api_gateway_app_router_with_prefix():
    # GIVEN a Router with registered routes
    # AND a prefix is defined during the registration
    app = ApiGatewayResolver()
    router = Router()

    @router.get(rule="/path")
    def foo():
        return {}

    app.include_router(router, prefix="/my")
    # WHEN calling the event handler after applying routes from router object
    result = app(LOAD_GW_EVENT, {})

    # THEN process event correctly
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]


def test_api_gateway_app_router_with_prefix_equals_path():
    # GIVEN a Router with registered routes
    # AND a prefix is defined during the registration
    app = ApiGatewayResolver()
    router = Router()

    @router.get(rule="/")
    def foo():
        return {}

    app.include_router(router, prefix="/my/path")
    # WHEN calling the event handler after applying routes from router object
    # WITH the request path matching the registration prefix
    result = app(LOAD_GW_EVENT, {})

    # THEN process event correctly
    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]


def test_api_gateway_app_router_with_different_methods():
    # GIVEN a Router with all the possible HTTP methods
    app = ApiGatewayResolver()
    router = Router()

    @router.get("/not_matching_get")
    def get_func():
        raise RuntimeError()

    @router.post("/no_matching_post")
    def post_func():
        raise RuntimeError()

    @router.put("/no_matching_put")
    def put_func():
        raise RuntimeError()

    @router.delete("/no_matching_delete")
    def delete_func():
        raise RuntimeError()

    @router.patch("/no_matching_patch")
    def patch_func():
        raise RuntimeError()

    app.include_router(router)

    # Also check check the route configurations
    routes = app._static_routes
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
    # THEN return a 404
    result = app(LOAD_GW_EVENT, None)
    assert result["statusCode"] == 404
    # AND cors headers are not returned
    assert "Access-Control-Allow-Origin" not in result["multiValueHeaders"]


def test_duplicate_routes():
    # GIVEN a duplicate routes
    app = ApiGatewayResolver()
    router = Router()

    @router.get("/my/path")
    def get_func_duplicate():
        raise RuntimeError()

    @app.get("/my/path")
    def get_func():
        return {}

    @router.get("/my/path")
    def get_func_another_duplicate():
        raise RuntimeError()

    app.include_router(router)

    # WHEN calling the handler
    result = app(LOAD_GW_EVENT, None)

    # THEN only execute the first registered route
    # AND print warnings
    assert result["statusCode"] == 200


def test_route_multiple_methods():
    # GIVEN a function with http methods passed as a list
    app = ApiGatewayResolver()
    req = "foo"
    get_event = deepcopy(LOAD_GW_EVENT)
    get_event["resource"] = "/accounts/{account_id}"
    get_event["path"] = f"/accounts/{req}"

    post_event = deepcopy(get_event)
    post_event["httpMethod"] = "POST"

    put_event = deepcopy(get_event)
    put_event["httpMethod"] = "PUT"

    lambda_context = {}

    @app.route(rule="/accounts/<account_id>", method=["GET", "POST"])
    def foo(account_id):
        assert app.lambda_context == lambda_context
        assert account_id == f"{req}"
        return {}

    # WHEN calling the event handler with the supplied methods
    get_result = app(get_event, lambda_context)
    post_result = app(post_event, lambda_context)
    put_result = app(put_event, lambda_context)

    # THEN events are processed correctly
    assert get_result["statusCode"] == 200
    assert get_result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    assert post_result["statusCode"] == 200
    assert post_result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    assert put_result["statusCode"] == 404
    assert put_result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]


def test_api_gateway_app_router_access_to_resolver():
    # GIVEN a Router with registered routes
    app = ApiGatewayResolver()
    router = Router()

    @router.get("/my/path")
    def foo():
        # WHEN accessing the api resolver instance via the router
        # THEN it is accessible and equal to the instantiated api resolver
        assert app == router.api_resolver
        return {}

    app.include_router(router)
    result = app(LOAD_GW_EVENT, {})

    assert result["statusCode"] == 200
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]


def test_exception_handler():
    # GIVEN a resolver with an exception handler defined for ValueError
    app = ApiGatewayResolver()

    @app.exception_handler(ValueError)
    def handle_value_error(ex: ValueError):
        print(f"request path is '{app.current_event.path}'")
        return Response(
            status_code=418,
            content_type=content_types.TEXT_HTML,
            body=str(ex),
        )

    @app.get("/my/path")
    def get_lambda() -> Response:
        raise ValueError("Foo!")

    # WHEN calling the event handler
    # AND a ValueError is raised
    result = app(LOAD_GW_EVENT, {})

    # THEN call the exception_handler
    assert result["statusCode"] == 418
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.TEXT_HTML]
    assert result["body"] == "Foo!"


def test_exception_handler_service_error():
    # GIVEN
    app = ApiGatewayResolver()

    @app.exception_handler(ServiceError)
    def service_error(ex: ServiceError):
        print(ex.msg)
        return Response(
            status_code=ex.status_code,
            content_type=content_types.APPLICATION_JSON,
            body="CUSTOM ERROR FORMAT",
        )

    @app.get("/my/path")
    def get_lambda() -> Response:
        raise InternalServerError("Something sensitive")

    # WHEN calling the event handler
    # AND a ServiceError is raised
    result = app(LOAD_GW_EVENT, {})

    # THEN call the exception_handler
    assert result["statusCode"] == 500
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    assert result["body"] == "CUSTOM ERROR FORMAT"


def test_exception_handler_not_found():
    # GIVEN a resolver with an exception handler defined for a 404 not found
    app = ApiGatewayResolver()

    @app.not_found
    def handle_not_found(exc: NotFoundError) -> Response:
        assert isinstance(exc, NotFoundError)
        return Response(status_code=404, content_type=content_types.TEXT_PLAIN, body="I am a teapot!")

    # WHEN calling the event handler
    # AND no route is found
    result = app(LOAD_GW_EVENT, {})

    # THEN call the exception_handler
    assert result["statusCode"] == 404
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.TEXT_PLAIN]
    assert result["body"] == "I am a teapot!"


def test_exception_handler_not_found_alt():
    # GIVEN a resolver with `@app.not_found()`
    app = ApiGatewayResolver()

    @app.not_found()
    def handle_not_found(_) -> Response:
        return Response(status_code=404, content_type=content_types.APPLICATION_JSON, body="{}")

    # WHEN calling the event handler
    # AND no route is found
    result = app(LOAD_GW_EVENT, {})

    # THEN call the @app.not_found() function
    assert result["statusCode"] == 404


def test_exception_handler_raises_service_error(json_dump):
    # GIVEN an exception handler raises a ServiceError (BadRequestError)
    app = ApiGatewayResolver()

    @app.exception_handler(ValueError)
    def client_error(ex: ValueError):
        raise BadRequestError("Bad request")

    @app.get("/my/path")
    def get_lambda() -> Response:
        raise ValueError("foo")

    # WHEN calling the event handler
    # AND a ValueError is raised
    result = app(LOAD_GW_EVENT, {})

    # THEN call the exception_handler
    assert result["statusCode"] == 400
    assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    expected = {"statusCode": 400, "message": "Bad request"}
    assert result["body"] == json_dump(expected)


def test_exception_handler_supports_list(json_dump):
    # GIVEN a resolver with an exception handler defined for a multiple exceptions in a list
    app = ApiGatewayResolver()
    event = deepcopy(LOAD_GW_EVENT)

    @app.exception_handler([ValueError, NotFoundError])
    def multiple_error(ex: Exception):
        raise BadRequestError("Bad request")

    @app.get("/path/a")
    def path_a() -> Response:
        raise ValueError("foo")

    @app.get("/path/b")
    def path_b() -> Response:
        raise NotFoundError

    # WHEN calling the app generating each exception
    for route in ["/path/a", "/path/b"]:
        event["path"] = route
        result = app(event, {})

        # THEN call the exception handler in the same way for both exceptions
        assert result["statusCode"] == 400
        assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
        expected = {"statusCode": 400, "message": "Bad request"}
        assert result["body"] == json_dump(expected)


def test_exception_handler_supports_multiple_decorators(json_dump):
    # GIVEN a resolver with an exception handler defined with multiple decorators
    app = ApiGatewayResolver()
    event = deepcopy(LOAD_GW_EVENT)

    @app.exception_handler(ValueError)
    @app.exception_handler(NotFoundError)
    def multiple_error(ex: Exception):
        raise BadRequestError("Bad request")

    @app.get("/path/a")
    def path_a() -> Response:
        raise ValueError("foo")

    @app.get("/path/b")
    def path_b() -> Response:
        raise NotFoundError

    # WHEN calling the app generating each exception
    for route in ["/path/a", "/path/b"]:
        event["path"] = route
        result = app(event, {})

        # THEN call the exception handler in the same way for both exceptions
        assert result["statusCode"] == 400
        assert result["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
        expected = {"statusCode": 400, "message": "Bad request"}
        assert result["body"] == json_dump(expected)


def test_event_source_compatibility():
    # GIVEN
    app = APIGatewayHttpResolver()

    @app.post("/my/path")
    def my_path():
        assert isinstance(app.current_event, APIGatewayProxyEventV2)
        return {}

    # WHEN
    @event_source(data_class=APIGatewayProxyEventV2)
    def handler(event: APIGatewayProxyEventV2, context):
        assert isinstance(event, APIGatewayProxyEventV2)
        return app.resolve(event, context)

    # THEN
    result = handler(load_event("apiGatewayProxyV2Event.json"), None)
    assert result["statusCode"] == 200


def test_response_with_status_code_only():
    ret = Response(status_code=204)
    assert ret.status_code == 204
    assert ret.body is None
    assert ret.headers == {}


def test_append_context():
    app = APIGatewayRestResolver()
    app.append_context(is_admin=True)
    assert app.context.get("is_admin") is True


def test_router_append_context():
    router = Router()
    router.append_context(is_admin=True)
    assert router.context.get("is_admin") is True


def test_route_context_is_cleared_after_resolve():
    # GIVEN a Http API V1 proxy type event
    app = APIGatewayRestResolver()
    app.append_context(is_admin=True)

    @app.get("/my/path")
    def my_path():
        return {"is_admin": app.context["is_admin"]}

    # WHEN event resolution kicks in
    app.resolve(LOAD_GW_EVENT, {})

    # THEN context should be empty
    assert app.context == {}


def test_router_has_access_to_app_context(json_dump):
    # GIVEN a Router with registered routes
    app = ApiGatewayResolver()
    router = Router()
    ctx = {"is_admin": True}

    @router.get("/my/path")
    def my_path():
        return {"is_admin": router.context["is_admin"]}

    app.include_router(router)

    # WHEN context is added and event resolution kicks in
    app.append_context(**ctx)
    ret = app.resolve(LOAD_GW_EVENT, {})

    # THEN response include initial context
    assert ret["body"] == json_dump(ctx)
    assert router.context == {}


def test_include_router_merges_context():
    # GIVEN
    app = APIGatewayRestResolver()
    router = Router()

    # WHEN
    app.append_context(is_admin=True)
    router.append_context(product_access=True)

    app.include_router(router)

    assert app.context == router.context


def test_nested_app_decorator():
    # GIVEN a Http API V1 proxy type event
    # with a function registered with two distinct routes
    app = APIGatewayRestResolver()

    @app.get("/my/path")
    @app.get("/my/anotherPath")
    def get_lambda() -> Response:
        return Response(200, content_types.APPLICATION_JSON, json.dumps({"foo": "value"}))

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})
    result2 = app(load_event("apiGatewayProxyEventAnotherPath.json"), {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result2["statusCode"] == 200


def test_nested_router_decorator():
    # GIVEN a Http API V1 proxy type event
    # with a function registered with two distinct routes
    app = APIGatewayRestResolver()
    router = Router()

    @router.get("/my/path")
    @router.get("/my/anotherPath")
    def get_lambda() -> Response:
        return Response(200, content_types.APPLICATION_JSON, json.dumps({"foo": "value"}))

    app.include_router(router)

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})
    result2 = app(load_event("apiGatewayProxyEventAnotherPath.json"), {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result2["statusCode"] == 200


def test_dict_response():
    # GIVEN a dict is returned
    app = ApiGatewayResolver()

    @app.get("/lambda")
    def get_message():
        return {"message": "success"}

    # WHEN calling handler
    response = app({"httpMethod": "GET", "path": "/lambda"}, None)

    # THEN the body is correctly formatted, the status code is 200 and the content type is json
    assert response["statusCode"] == 200
    assert response["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    response_body = json.loads(response["body"])
    assert response_body["message"] == "success"


def test_dict_response_with_status_code():
    # GIVEN a dict is returned with a status code
    app = ApiGatewayResolver()

    @app.get("/lambda")
    def get_message():
        return {"message": "success"}, 201

    # WHEN calling handler
    response = app({"httpMethod": "GET", "path": "/lambda"}, None)

    # THEN the body is correctly formatted, the status code is 201 and the content type is json
    assert response["statusCode"] == 201
    assert response["multiValueHeaders"]["Content-Type"] == [content_types.APPLICATION_JSON]
    response_body = json.loads(response["body"])
    assert response_body["message"] == "success"


def test_route_match_prioritize_full_match():
    # GIVEN a Http API V1, with a function registered with two routes
    app = APIGatewayRestResolver()
    router = Router()

    @router.get("/my/{path}")
    def dynamic_handler() -> Response:
        return Response(200, content_types.APPLICATION_JSON, json.dumps({"hello": "dynamic"}))

    @router.get("/my/path")
    def static_handler() -> Response:
        return Response(200, content_types.APPLICATION_JSON, json.dumps({"hello": "static"}))

    app.include_router(router)

    # WHEN calling the event handler with /foo/dynamic
    response = app(LOAD_GW_EVENT, {})

    # THEN the static_handler should have been called, because it fully matches the path directly
    response_body = json.loads(response["body"])
    assert response_body["hello"] == "static"
