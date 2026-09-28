from __future__ import annotations

import asyncio
import base64
import gzip
import json
import random

import pytest

from aws_lambda_powertools.event_handler import (
    ALBResolver,
    APIGatewayHttpResolver,
    APIGatewayRestResolver,
    CORSConfig,
    Response,
    content_types,
)
from aws_lambda_powertools.event_handler.exceptions import InternalServerError, ResponseSizeExceededError
from aws_lambda_powertools.shared.cookies import Cookie
from tests.functional.utils import load_event

MAX_RESPONSE_SIZE = 1024 * 1024


@pytest.fixture(autouse=True)
def lambda_runtime_environment(monkeypatch):
    monkeypatch.setenv("AWS_EXECUTION_ENV", "AWS_Lambda_python3.14")
    monkeypatch.delenv("POWERTOOLS_DEV", raising=False)


@pytest.fixture
def alb_event():
    return load_event("albEvent.json")


@pytest.fixture(params=["sync", "async"])
def resolve_response(request):
    def resolve(app, event):
        if request.param == "async":
            return asyncio.run(app.resolve_async(event, {}))
        return app.resolve(event, {})

    return resolve


def make_app(body, *, enabled=True, compress=False, **response_options):
    app = ALBResolver(enable_response_size_validation=enabled)

    @app.get("/lambda", compress=compress)
    def get_response():
        return Response(200, content_types.TEXT_PLAIN, body, **response_options)

    return app


def response_size(response, *, ensure_ascii=False):
    return len(json.dumps(response, ensure_ascii=ensure_ascii).encode("utf-8"))


def test_response_size_validation_is_disabled_by_default(alb_event, resolve_response):
    app = ALBResolver()

    @app.get("/lambda")
    def get_response():
        return Response(200, content_types.TEXT_PLAIN, "x" * MAX_RESPONSE_SIZE)

    response = resolve_response(app, alb_event)
    assert response["statusCode"] == 200
    assert response_size(response) > MAX_RESPONSE_SIZE


def test_response_size_validation_can_be_disabled_explicitly(alb_event, resolve_response):
    app = make_app("x" * MAX_RESPONSE_SIZE, enabled=False)
    assert response_size(resolve_response(app, alb_event)) > MAX_RESPONSE_SIZE


@pytest.mark.parametrize("offset", [-1, 0, 1], ids=["below-limit", "at-limit", "above-limit"])
def test_response_size_boundary_includes_the_envelope(alb_event, resolve_response, offset):
    envelope = {
        "statusCode": 200,
        "body": "",
        "isBase64Encoded": False,
        "headers": {"Content-Type": content_types.TEXT_PLAIN},
    }
    body = "x" * (MAX_RESPONSE_SIZE - response_size(envelope) + offset)
    app = make_app(body)

    if offset <= 0:
        response = resolve_response(app, alb_event)
        assert response_size(response) == MAX_RESPONSE_SIZE + offset
    else:
        with pytest.raises(ResponseSizeExceededError) as raised:
            resolve_response(app, alb_event)
        assert raised.value.actual_size == MAX_RESPONSE_SIZE + offset
        assert raised.value.max_size == MAX_RESPONSE_SIZE
        assert app.context == {}


@pytest.mark.parametrize(
    "execution_env,ensure_ascii",
    [
        (None, True),
        ("AWS_Lambda_python3.10", True),
        ("AWS_Lambda_python3.11", True),
        ("AWS_Lambda_python3.12", False),
        ("AWS_Lambda_python3.14", False),
    ],
)
def test_response_size_matches_runtime_unicode_encoding(
    alb_event,
    resolve_response,
    monkeypatch,
    execution_env,
    ensure_ascii,
):
    if execution_env is None:
        monkeypatch.delenv("AWS_EXECUTION_ENV")
    else:
        monkeypatch.setenv("AWS_EXECUTION_ENV", execution_env)

    body = "é" * 200_000
    expected = resolve_response(make_app(body, enabled=False), alb_event)
    size = response_size(expected, ensure_ascii=ensure_ascii)

    if ensure_ascii:
        assert size > MAX_RESPONSE_SIZE
        with pytest.raises(ResponseSizeExceededError) as raised:
            resolve_response(make_app(body), alb_event)
        assert raised.value.actual_size == size
    else:
        assert size < MAX_RESPONSE_SIZE
        assert resolve_response(make_app(body), alb_event) == expected


def test_json_escaping_is_included_in_response_size(alb_event, resolve_response):
    body = '"\\\n' * (MAX_RESPONSE_SIZE // 4)
    assert len(body.encode("utf-8")) < MAX_RESPONSE_SIZE
    expected = resolve_response(make_app(body, enabled=False), alb_event)

    with pytest.raises(ResponseSizeExceededError) as raised:
        resolve_response(make_app(body), alb_event)

    assert raised.value.actual_size == response_size(expected)
    assert raised.value.actual_size > MAX_RESPONSE_SIZE


@pytest.mark.parametrize("multi_value_headers", [False, True])
def test_response_size_includes_serialized_headers_and_cookies(alb_event, resolve_response, multi_value_headers):
    if multi_value_headers:
        alb_event["multiValueHeaders"] = {name: [value] for name, value in alb_event.pop("headers").items()}
    body = "x" * (MAX_RESPONSE_SIZE - 500)
    options = {"headers": {"X-Extra": "h" * 300}, "cookies": [Cookie("session", "c" * 300)]}
    expected = resolve_response(make_app(body, enabled=False, **options), alb_event)

    with pytest.raises(ResponseSizeExceededError) as raised:
        resolve_response(make_app(body, **options), alb_event)

    assert len(body.encode("utf-8")) < MAX_RESPONSE_SIZE
    assert raised.value.actual_size == response_size(expected)
    assert raised.value.actual_size > MAX_RESPONSE_SIZE
    headers_key = "multiValueHeaders" if multi_value_headers else "headers"
    assert "Set-Cookie" in expected[headers_key]


def test_response_size_is_checked_after_base64_encoding(alb_event, resolve_response):
    body = b"\x00" * (MAX_RESPONSE_SIZE * 3 // 4)
    expected = resolve_response(make_app(body, enabled=False), alb_event)
    assert expected["isBase64Encoded"] is True
    assert len(body) < MAX_RESPONSE_SIZE

    with pytest.raises(ResponseSizeExceededError) as raised:
        resolve_response(make_app(body), alb_event)

    assert raised.value.actual_size == response_size(expected)


def test_compression_can_bring_a_response_below_the_limit(alb_event, resolve_response):
    body = "x" * (MAX_RESPONSE_SIZE * 2)
    response = resolve_response(make_app(body, compress=True), alb_event)

    assert response["headers"]["Content-Encoding"] == "gzip"
    assert response["isBase64Encoded"] is True
    assert gzip.decompress(base64.b64decode(response["body"])).decode() == body
    assert response_size(response) < MAX_RESPONSE_SIZE


def test_compressed_responses_are_still_validated(alb_event, resolve_response):
    body = random.Random(42).randbytes(MAX_RESPONSE_SIZE * 3 // 4)
    expected = resolve_response(make_app(body, enabled=False, compress=True), alb_event)
    assert expected["headers"]["Content-Encoding"] == "gzip"

    with pytest.raises(ResponseSizeExceededError) as raised:
        resolve_response(make_app(body, compress=True), alb_event)

    assert raised.value.actual_size == response_size(expected)
    assert raised.value.actual_size > MAX_RESPONSE_SIZE


def test_custom_body_serializer_runs_before_response_size_validation(alb_event, resolve_response):
    serialized_bodies = []

    def serialize(body):
        serialized_bodies.append(body)
        return "x" * MAX_RESPONSE_SIZE

    app = ALBResolver(enable_response_size_validation=True, serializer=serialize)

    @app.get("/lambda")
    def get_response():
        return {"small": "body"}

    with pytest.raises(ResponseSizeExceededError):
        resolve_response(app, alb_event)

    assert serialized_bodies == [{"small": "body"}]


@pytest.mark.parametrize("exception_type", [ResponseSizeExceededError, Exception])
def test_registered_handler_receives_size_error_with_route_context(alb_event, resolve_response, exception_type):
    origin = "https://example.com"
    alb_event["headers"]["origin"] = origin
    app = ALBResolver(cors=CORSConfig(allow_origin=origin), enable_response_size_validation=True)
    handled = []

    @app.get("/lambda", cors=True, cache_control="max-age=300")
    def get_response():
        return Response(200, content_types.TEXT_PLAIN, "x" * MAX_RESPONSE_SIZE)

    @app.exception_handler(exception_type)
    def handle_large_response(error):
        handled.append(error)
        assert app.context["_path"] == "/lambda"
        assert app.current_event.path == "/lambda"
        return Response(500, content_types.APPLICATION_JSON, {"message": "Response too large"})

    response = resolve_response(app, alb_event)

    assert response["statusCode"] == 500
    assert json.loads(response["body"]) == {"message": "Response too large"}
    assert response["headers"]["Access-Control-Allow-Origin"] == origin
    assert response["headers"]["Cache-Control"] == "no-cache"
    assert len(handled) == 1
    assert isinstance(handled[0], ResponseSizeExceededError)
    assert handled[0].actual_size > handled[0].max_size == MAX_RESPONSE_SIZE
    assert app.context == {}


@pytest.mark.parametrize("debug", [False, True])
def test_unhandled_size_errors_propagate_even_in_debug_mode(alb_event, resolve_response, debug):
    app = ALBResolver(enable_response_size_validation=True, debug=debug)

    @app.get("/lambda")
    def get_response():
        return Response(200, content_types.TEXT_PLAIN, "customer-secret" + "x" * MAX_RESPONSE_SIZE)

    with pytest.raises(ResponseSizeExceededError) as raised:
        resolve_response(app, alb_event)

    assert str(raised.value.actual_size) in str(raised.value)
    assert str(MAX_RESPONSE_SIZE) in str(raised.value)
    assert "customer-secret" not in str(raised.value)
    assert app.context == {}


def test_oversized_handler_response_does_not_recurse(alb_event, resolve_response):
    app = make_app("x" * MAX_RESPONSE_SIZE)
    handled = []

    @app.exception_handler(ResponseSizeExceededError)
    def handle_large_response(error):
        handled.append(error)
        return Response(500, content_types.TEXT_PLAIN, "y" * (MAX_RESPONSE_SIZE + 10))

    with pytest.raises(ResponseSizeExceededError) as raised:
        resolve_response(app, alb_event)

    assert len(handled) == 1
    assert raised.value.actual_size == handled[0].actual_size + 10
    assert app.context == {}


def test_exceptions_raised_by_size_handler_propagate(alb_event, resolve_response):
    app = make_app("x" * MAX_RESPONSE_SIZE)

    @app.exception_handler(ResponseSizeExceededError)
    def handle_large_response(error):
        raise ValueError("handler failure")

    with pytest.raises(ValueError, match="handler failure"):
        resolve_response(app, alb_event)

    assert app.context == {}


def test_size_handler_can_raise_a_service_error(alb_event, resolve_response):
    app = make_app("x" * MAX_RESPONSE_SIZE)

    @app.exception_handler(ResponseSizeExceededError)
    def handle_large_response(error):
        raise InternalServerError("Response too large")

    response = resolve_response(app, alb_event)

    assert response["statusCode"] == 500
    assert json.loads(response["body"]) == {"statusCode": 500, "message": "Response too large"}


def test_size_handler_empty_body_is_normalized_for_alb(alb_event, resolve_response):
    app = make_app("x" * MAX_RESPONSE_SIZE)

    @app.exception_handler(ResponseSizeExceededError)
    def handle_large_response(error):
        return Response(status_code=500)

    response = resolve_response(app, alb_event)

    assert response["statusCode"] == 500
    assert response["body"] == ""


def test_not_found_responses_are_validated(alb_event, resolve_response):
    app = ALBResolver(enable_response_size_validation=True)

    @app.not_found
    def handle_not_found(error):
        return Response(404, content_types.TEXT_PLAIN, "x" * MAX_RESPONSE_SIZE)

    with pytest.raises(ResponseSizeExceededError):
        resolve_response(app, alb_event)


def test_responses_from_other_exception_handlers_are_validated(alb_event, resolve_response):
    app = ALBResolver(enable_response_size_validation=True)
    handled = []

    @app.get("/lambda")
    def get_response():
        raise ValueError("route failure")

    @app.exception_handler(ValueError)
    def handle_route_error(error):
        return Response(500, content_types.TEXT_PLAIN, "x" * MAX_RESPONSE_SIZE)

    @app.exception_handler(ResponseSizeExceededError)
    def handle_large_response(error):
        handled.append(error)
        return Response(500, content_types.TEXT_PLAIN, "Small error response")

    response = resolve_response(app, alb_event)

    assert response["body"] == "Small error response"
    assert len(handled) == 1


def test_middleware_response_changes_are_validated(alb_event, resolve_response):
    app = make_app("small")

    def enlarge_response(app, next_middleware):
        response = next_middleware(app)
        response.body = "x" * MAX_RESPONSE_SIZE
        return response

    app.use([enlarge_response])

    with pytest.raises(ResponseSizeExceededError):
        resolve_response(app, alb_event)


def test_native_async_handler_size_error_can_be_handled(alb_event):
    app = ALBResolver(enable_response_size_validation=True)

    @app.get("/lambda")
    async def get_response():
        await asyncio.sleep(0)
        return Response(200, content_types.TEXT_PLAIN, "x" * MAX_RESPONSE_SIZE)

    @app.exception_handler(ResponseSizeExceededError)
    def handle_large_response(error):
        return Response(500, content_types.TEXT_PLAIN, "Small error response")

    response = asyncio.run(app.resolve_async(alb_event, {}))

    assert response["statusCode"] == 500
    assert response["body"] == "Small error response"


@pytest.mark.parametrize(
    "resolver,event_name",
    [
        (APIGatewayRestResolver, "apiGatewayProxyEvent.json"),
        (APIGatewayHttpResolver, "apiGatewayProxyV2Event_GET.json"),
    ],
)
def test_alb_response_limit_does_not_apply_to_api_gateway(resolver, event_name, resolve_response):
    app = resolver()
    event = load_event(event_name)
    if "rawPath" in event:
        event["rawPath"] = "/large"
        event["requestContext"]["http"]["path"] = "/large"
        event["requestContext"]["http"]["method"] = "GET"
    else:
        event["path"] = "/large"
        event["httpMethod"] = "GET"

    @app.get("/large")
    def get_response():
        return Response(200, content_types.TEXT_PLAIN, "x" * MAX_RESPONSE_SIZE)

    response = resolve_response(app, event)

    assert response["statusCode"] == 200
    assert response_size(response) > MAX_RESPONSE_SIZE
