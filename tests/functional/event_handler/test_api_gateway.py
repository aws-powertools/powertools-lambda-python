import base64
import json
import zlib
from decimal import Decimal
from pathlib import Path
from typing import Dict

from aws_lambda_powertools.event_handler.api_gateway import (
    APPLICATION_JSON,
    ApiGatewayResolver,
    BadRequestError,
    CORSConfig,
    InternalServerError,
    NotFoundError,
    ProxyEventType,
    Response,
    ResponseBuilder,
    ServiceError,
    UnauthorizedError,
)
from aws_lambda_powertools.shared.json_encoder import Encoder
from aws_lambda_powertools.utilities.data_classes import ALBEvent, APIGatewayProxyEvent, APIGatewayProxyEventV2
from tests.functional.utils import load_event


def read_media(file_name: str) -> bytes:
    path = Path(str(Path(__file__).parent.parent.parent.parent) + "/docs/media/" + file_name)
    return path.read_bytes()


LOAD_GW_EVENT = load_event("apiGatewayProxyEvent.json")
TEXT_HTML = "text/html"


def test_alb_event():
    # GIVEN a Application Load Balancer proxy type event
    app = ApiGatewayResolver(proxy_type=ProxyEventType.ALBEvent)

    @app.get("/lambda")
    def foo():
        assert isinstance(app.current_event, ALBEvent)
        assert app.lambda_context == {}
        return Response(200, TEXT_HTML, "foo")

    # WHEN calling the event handler
    result = app(load_event("albEvent.json"), {})

    # THEN process event correctly
    # AND set the current_event type as ALBEvent
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == TEXT_HTML
    assert result["body"] == "foo"


def test_api_gateway_v1():
    # GIVEN a Http API V1 proxy type event
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)

    @app.get("/my/path")
    def get_lambda() -> Response:
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        assert app.lambda_context == {}
        return Response(200, APPLICATION_JSON, json.dumps({"foo": "value"}))

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == APPLICATION_JSON


def test_api_gateway():
    # GIVEN a Rest API Gateway proxy type event
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)

    @app.get("/my/path")
    def get_lambda() -> Response:
        assert isinstance(app.current_event, APIGatewayProxyEvent)
        return Response(200, TEXT_HTML, "foo")

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN process event correctly
    # AND set the current_event type as APIGatewayProxyEvent
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == TEXT_HTML
    assert result["body"] == "foo"


def test_api_gateway_v2():
    # GIVEN a Http API V2 proxy type event
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEventV2)

    @app.post("/my/path")
    def my_path() -> Response:
        assert isinstance(app.current_event, APIGatewayProxyEventV2)
        post_data = app.current_event.json_body
        return Response(200, "plain/text", post_data["username"])

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
    def get_lambda(my_id: str, name: str) -> Response:
        assert name == "my"
        return Response(200, TEXT_HTML, my_id)

    # WHEN calling the event handler
    result = app(LOAD_GW_EVENT, {})

    # THEN
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == TEXT_HTML
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
    # THEN return a 404
    result = handler(LOAD_GW_EVENT, None)
    assert result["statusCode"] == 404
    # AND cors headers are not returned
    assert "Access-Control-Allow-Origin" not in result["headers"]


def test_cors():
    # GIVEN a function with cors=True
    # AND http method set to GET
    app = ApiGatewayResolver()

    @app.get("/my/path", cors=True)
    def with_cors() -> Response:
        return Response(200, TEXT_HTML, "test")

    @app.get("/without-cors")
    def without_cors() -> Response:
        return Response(200, TEXT_HTML, "test")

    def handler(event, context):
        return app.resolve(event, context)

    # WHEN calling the event handler
    result = handler(LOAD_GW_EVENT, None)

    # THEN the headers should include cors headers
    assert "headers" in result
    headers = result["headers"]
    assert headers["Content-Type"] == TEXT_HTML
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert "Access-Control-Allow-Credentials" not in headers
    assert headers["Access-Control-Allow-Headers"] == ",".join(sorted(CORSConfig._REQUIRED_HEADERS))

    # THEN for routes without cors flag return no cors headers
    mock_event = {"path": "/my/request", "httpMethod": "GET"}
    result = handler(mock_event, None)
    assert "Access-Control-Allow-Origin" not in result["headers"]


def test_compress():
    # GIVEN a function that has compress=True
    # AND an event with a "Accept-Encoding" that include gzip
    app = ApiGatewayResolver()
    mock_event = {"path": "/my/request", "httpMethod": "GET", "headers": {"Accept-Encoding": "deflate, gzip"}}
    expected_value = '{"test": "value"}'

    @app.get("/my/request", compress=True)
    def with_compression() -> Response:
        return Response(200, APPLICATION_JSON, expected_value)

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
    def read_image() -> Response:
        return Response(200, "image/png", read_media("idempotent_sequence_exception.png"))

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
    def return_text() -> Response:
        return Response(200, "text/plain", expected_value)

    # WHEN calling the event handler
    result = app({"path": "/my/path", "httpMethod": "GET", "headers": {}}, None)

    # THEN don't perform any gzip compression
    assert result["isBase64Encoded"] is False
    assert result["body"] == expected_value


def test_cache_control_200():
    # GIVEN a function with cache_control set
    app = ApiGatewayResolver()

    @app.get("/success", cache_control="max-age=600")
    def with_cache_control() -> Response:
        return Response(200, TEXT_HTML, "has 200 response")

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
    def with_cache_control_has_500() -> Response:
        return Response(503, TEXT_HTML, "has 503 response")

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
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)
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
    app = ApiGatewayResolver(proxy_type=ProxyEventType.APIGatewayProxyEvent)

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
    event = {"path": "/cors", "httpMethod": "GET"}

    @app.get("/cors")
    def get_with_cors():
        return {}

    @app.get("/another-one", cors=False)
    def another_one():
        return {}

    # WHEN calling the event handler
    result = app(event, None)

    # THEN routes by default return the custom cors headers
    assert "headers" in result
    headers = result["headers"]
    assert headers["Content-Type"] == APPLICATION_JSON
    assert headers["Access-Control-Allow-Origin"] == cors_config.allow_origin
    expected_allows_headers = ",".join(sorted(set(allow_header + cors_config._REQUIRED_HEADERS)))
    assert headers["Access-Control-Allow-Headers"] == expected_allows_headers
    assert headers["Access-Control-Expose-Headers"] == ",".join(cors_config.expose_headers)
    assert headers["Access-Control-Max-Age"] == str(cors_config.max_age)
    assert "Access-Control-Allow-Credentials" in headers
    assert headers["Access-Control-Allow-Credentials"] == "true"

    # AND custom cors was set on the app
    assert isinstance(app._cors, CORSConfig)
    assert app._cors is cors_config

    # AND routes without cors don't include "Access-Control" headers
    event = {"path": "/another-one", "httpMethod": "GET"}
    result = app(event, None)
    headers = result["headers"]
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
    headers = result["headers"]
    assert "Content-Type" not in headers


def test_no_matches_with_cors():
    # GIVEN an event that does not match any of the given routes
    # AND cors enabled
    app = ApiGatewayResolver(cors=CORSConfig())

    # WHEN calling the handler
    result = app({"path": "/another-one", "httpMethod": "GET"}, None)

    # THEN return a 404
    # AND cors headers are returned
    assert result["statusCode"] == 404
    assert "Access-Control-Allow-Origin" in result["headers"]
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
    result = app({"path": "/foo", "httpMethod": "OPTIONS"}, None)

    # THEN return no content
    # AND include Access-Control-Allow-Methods of the cors methods used
    assert result["statusCode"] == 204
    assert result["body"] is None
    headers = result["headers"]
    assert "Content-Type" not in headers
    assert "Access-Control-Allow-Origin" in result["headers"]
    assert headers["Access-Control-Allow-Methods"] == "DELETE,GET,OPTIONS"


def test_custom_preflight_response():
    # GIVEN cors is enabled
    # AND we have a custom preflight method
    # AND the request matches this custom preflight route
    app = ApiGatewayResolver(cors=CORSConfig())

    @app.route(method="OPTIONS", rule="/some-call", cors=True)
    def custom_preflight():
        return Response(
            status_code=200,
            content_type=TEXT_HTML,
            body="Foo",
            headers={"Access-Control-Allow-Methods": "CUSTOM"},
        )

    @app.route(method="CUSTOM", rule="/some-call", cors=True)
    def custom_method():
        ...

    # WHEN calling the handler
    result = app({"path": "/some-call", "httpMethod": "OPTIONS"}, None)

    # THEN return the custom preflight response
    assert result["statusCode"] == 200
    assert result["body"] == "Foo"
    headers = result["headers"]
    assert headers["Content-Type"] == TEXT_HTML
    assert "Access-Control-Allow-Origin" in result["headers"]
    assert headers["Access-Control-Allow-Methods"] == "CUSTOM"


def test_service_error_response():
    # GIVEN a service error response
    app = ApiGatewayResolver(cors=CORSConfig())

    @app.route(method="GET", rule="/bad-request-error", cors=False)
    def bad_request_error():
        raise BadRequestError("Missing required parameter")

    @app.route(method="GET", rule="/unauthorized-error", cors=False)
    def unauthorized_error():
        raise UnauthorizedError("Unauthorized")

    @app.route(method="GET", rule="/service-error", cors=True)
    def service_error():
        raise ServiceError(403, "Unauthorized")

    @app.route(method="GET", rule="/not-found-error", cors=False)
    def not_found_error():
        raise NotFoundError

    @app.route(method="GET", rule="/internal-server-error", cors=False)
    def internal_server_error():
        raise InternalServerError("Internal server error")

    # WHEN calling the handler
    # AND path is /bad-request-error
    result = app({"path": "/bad-request-error", "httpMethod": "GET"}, None)
    # THEN return the bad request error response
    # AND status code equals 400
    assert result["statusCode"] == 400
    assert result["body"] == json.dumps({"message": "Missing required parameter"})
    assert result["headers"]["Content-Type"] == APPLICATION_JSON

    # WHEN calling the handler
    # AND path is /unauthorized-error
    result = app({"path": "/unauthorized-error", "httpMethod": "GET"}, None)
    # THEN return the unauthorized error response
    # AND status code equals 401
    assert result["statusCode"] == 401
    assert result["body"] == json.dumps({"message": "Unauthorized"})
    assert result["headers"]["Content-Type"] == APPLICATION_JSON

    # WHEN calling the handler
    # AND path is /service-error
    result = app({"path": "/service-error", "httpMethod": "GET"}, None)
    # THEN return the service error response
    # AND status code equals 403
    assert result["statusCode"] == 403
    assert result["body"] == json.dumps({"message": "Unauthorized"})
    assert result["headers"]["Content-Type"] == APPLICATION_JSON
    assert "Access-Control-Allow-Origin" in result["headers"]

    # WHEN calling the handler
    # AND path is /not-found-error
    result = app({"path": "/not-found-error", "httpMethod": "GET"}, None)
    # THEN return the not found error response
    # AND status code equals 404
    assert result["statusCode"] == 404
    assert result["body"] == json.dumps({"message": "Not found"})
    assert result["headers"]["Content-Type"] == APPLICATION_JSON

    # WHEN calling the handler
    # AND path is /internal-server-error
    result = app({"path": "/internal-server-error", "httpMethod": "GET"}, None)
    # THEN return the internal server error response
    # AND status code equals 500
    assert result["statusCode"] == 500
    assert result["body"] == json.dumps({"message": "Internal server error"})
    assert result["headers"]["Content-Type"] == APPLICATION_JSON
