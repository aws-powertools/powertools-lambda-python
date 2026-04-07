"""Integration tests for Lambda Metadata Service – exercises the real HTTP path."""

from __future__ import annotations

import http.server
import json
from collections import namedtuple

import pytest

from aws_lambda_powertools.utilities.metadata import (
    LambdaMetadataError,
    clear_metadata_cache,
    get_lambda_metadata,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_metadata_cache()
    yield
    clear_metadata_cache()


@pytest.fixture
def lambda_context():
    context = {
        "function_name": "test",
        "memory_limit_in_mb": 128,
        "invoked_function_arn": "arn:aws:lambda:eu-west-1:123456789012:function:test",
        "aws_request_id": "52fdfc07-2182-154f-163f-5f0f9a621d72",
    }
    return namedtuple("LambdaContext", context.keys())(*context.values())


@pytest.fixture
def lambda_event():
    return {"key": "value"}


# ---------------------------------------------------------------------------
# HTTP server fixtures
# ---------------------------------------------------------------------------


def _make_handler(status: int, body: str):
    """Create an HTTP handler that returns a fixed status and body."""

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, format, *args):  # noqa: A002
            pass

    return Handler


@pytest.fixture
def metadata_server(monkeypatch):
    """Start a local HTTP server returning valid metadata and set env vars."""
    body = json.dumps({"AvailabilityZoneID": "use1-az1"})
    server = http.server.HTTPServer(("127.0.0.1", 0), _make_handler(200, body))
    port = server.server_address[1]

    import threading

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    monkeypatch.setenv("AWS_LAMBDA_INITIALIZATION_TYPE", "on-demand")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_API", f"127.0.0.1:{port}")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_TOKEN", "test-token")

    yield server
    server.shutdown()


@pytest.fixture
def error_server(monkeypatch):
    """Start a local HTTP server returning 500 and set env vars."""
    server = http.server.HTTPServer(("127.0.0.1", 0), _make_handler(500, "Internal Server Error"))
    port = server.server_address[1]

    import threading

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    monkeypatch.setenv("AWS_LAMBDA_INITIALIZATION_TYPE", "on-demand")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_API", f"127.0.0.1:{port}")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_TOKEN", "test-token")

    yield server
    server.shutdown()


@pytest.fixture
def invalid_json_server(monkeypatch):
    """Start a local HTTP server returning invalid JSON."""
    server = http.server.HTTPServer(("127.0.0.1", 0), _make_handler(200, "not-json"))
    port = server.server_address[1]

    import threading

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    monkeypatch.setenv("AWS_LAMBDA_INITIALIZATION_TYPE", "on-demand")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_API", f"127.0.0.1:{port}")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_TOKEN", "test-token")

    yield server
    server.shutdown()


# ---------------------------------------------------------------------------
# Tests – happy path
# ---------------------------------------------------------------------------


def test_fetch_metadata_returns_az_id(lambda_context, lambda_event, metadata_server):
    # GIVEN a Lambda environment pointing to a local metadata endpoint
    def lambda_handler(event, context):
        return get_lambda_metadata()

    # WHEN the handler is invoked
    result = lambda_handler(lambda_event, lambda_context)

    # THEN it returns metadata with the availability zone id
    assert result.availability_zone_id == "use1-az1"


def test_fetch_metadata_caches_across_invocations(lambda_context, lambda_event, metadata_server):
    # GIVEN a Lambda environment pointing to a local metadata endpoint
    def lambda_handler(event, context):
        return get_lambda_metadata()

    # WHEN the handler is invoked twice (warm start)
    first = lambda_handler(lambda_event, lambda_context)
    second = lambda_handler(lambda_event, lambda_context)

    # THEN both return the same data
    assert first.availability_zone_id == "use1-az1"
    assert second.availability_zone_id == "use1-az1"


# ---------------------------------------------------------------------------
# Tests – error paths
# ---------------------------------------------------------------------------


def test_fetch_metadata_raises_on_http_500(lambda_context, lambda_event, error_server):
    # GIVEN a Lambda environment where the endpoint returns 500
    def lambda_handler(event, context):
        return get_lambda_metadata()

    # WHEN the handler is invoked
    # THEN it raises LambdaMetadataError with status code 500
    with pytest.raises(LambdaMetadataError, match="status 500") as exc_info:
        lambda_handler(lambda_event, lambda_context)

    assert exc_info.value.status_code == 500


def test_fetch_metadata_raises_on_invalid_json(lambda_context, lambda_event, invalid_json_server):
    # GIVEN a Lambda environment where the endpoint returns invalid JSON
    def lambda_handler(event, context):
        return get_lambda_metadata()

    # WHEN the handler is invoked
    # THEN it raises LambdaMetadataError about parsing
    with pytest.raises(LambdaMetadataError, match="Failed to parse"):
        lambda_handler(lambda_event, lambda_context)


def test_fetch_metadata_raises_on_unreachable_endpoint(lambda_context, lambda_event, monkeypatch):
    # GIVEN a Lambda environment pointing to an unreachable endpoint
    monkeypatch.setenv("AWS_LAMBDA_INITIALIZATION_TYPE", "on-demand")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_API", "127.0.0.1:1")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_TOKEN", "test-token")

    def lambda_handler(event, context):
        return get_lambda_metadata(timeout=0.1)

    # WHEN the handler is invoked
    # THEN it raises LambdaMetadataError about connection failure
    with pytest.raises(LambdaMetadataError, match="Failed to fetch"):
        lambda_handler(lambda_event, lambda_context)
