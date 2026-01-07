"""Tests for OpenAPI merge functionality."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi import OpenAPIMerge, OpenAPIMergeError

MERGE_HANDLERS_PATH = Path(__file__).parent / "merge_handlers"


def test_openapi_merge_discover_non_recursive():
    # GIVEN an OpenAPIMerge instance
    merge = OpenAPIMerge(title="Non-Recursive API", version="1.0.0")

    # WHEN discovering resolvers without recursion
    files = merge.discover(
        path=MERGE_HANDLERS_PATH,
        pattern="*_handler.py",
        recursive=False,
    )

    # THEN it should find handlers in the root directory only
    assert len(files) > 0
    for f in files:
        assert f.parent == MERGE_HANDLERS_PATH


def test_openapi_merge_discover_and_get_schema():
    # GIVEN an OpenAPIMerge instance
    merge = OpenAPIMerge(title="My API", version="1.0.0")

    # WHEN discovering resolvers
    merge.discover(
        path=MERGE_HANDLERS_PATH,
        pattern="**/*_handler.py",
        exclude=["**/conflict_handler.py"],
        resolver_name="app",
    )

    # THEN it should generate merged schema
    schema = merge.get_openapi_schema()
    assert schema["info"]["title"] == "My API"
    assert schema["info"]["version"] == "1.0.0"
    assert "/users" in schema["paths"]
    assert "/orders" in schema["paths"]


def test_openapi_merge_get_json_schema():
    # GIVEN an OpenAPIMerge with discovered resolvers
    merge = OpenAPIMerge(title="JSON API", version="2.0.0")
    merge.discover(
        path=MERGE_HANDLERS_PATH,
        pattern="**/users_handler.py",
    )

    # WHEN getting JSON schema
    json_schema = merge.get_openapi_json_schema()

    # THEN it should be valid JSON
    parsed = json.loads(json_schema)
    assert parsed["info"]["title"] == "JSON API"
    assert "/users" in parsed["paths"]


def test_openapi_merge_discovered_files():
    # GIVEN an OpenAPIMerge with discovered files
    merge = OpenAPIMerge(title="Test", version="1.0.0")
    merge.discover(path=MERGE_HANDLERS_PATH, pattern="**/users_handler.py")

    # WHEN getting discovered files
    files = merge.discovered_files

    # THEN it should return the list
    assert len(files) == 1
    assert files[0].name == "users_handler.py"


def test_openapi_merge_on_conflict_error():
    # GIVEN handlers with conflicting routes
    merge = OpenAPIMerge(
        title="Conflict API",
        version="1.0.0",
        on_conflict="error",
    )
    merge.discover(
        path=MERGE_HANDLERS_PATH,
        pattern="**/*_handler.py",  # includes conflict_handler.py
        resolver_name="app",
    )

    # WHEN/THEN getting schema should raise
    with pytest.raises(OpenAPIMergeError, match="Conflict"):
        merge.get_openapi_schema()


def test_openapi_merge_on_conflict_warn():
    # GIVEN handlers with conflicting routes
    merge = OpenAPIMerge(title="Warn API", version="1.0.0", on_conflict="warn")
    merge.discover(
        path=MERGE_HANDLERS_PATH,
        pattern="**/*_handler.py",
        resolver_name="app",
    )

    # WHEN getting schema with mock logger
    with patch("aws_lambda_powertools.event_handler.openapi.merge.logger") as mock_logger:
        schema = merge.get_openapi_schema()

    # THEN it should log warning and keep first
    mock_logger.warning.assert_called()
    assert "/users" in schema["paths"]


def test_openapi_merge_on_conflict_last():
    # GIVEN handlers with conflicting routes (zzz_ prefix ensures it's discovered last)
    merge = OpenAPIMerge(title="Last API", version="1.0.0", on_conflict="last")
    merge.discover(
        path=MERGE_HANDLERS_PATH,
        pattern=["**/users_handler.py", "**/zzz_conflict_last_handler.py"],
        resolver_name="app",
    )

    # WHEN getting schema
    schema = merge.get_openapi_schema()

    # THEN it should use last definition
    assert "/users" in schema["paths"]
    assert schema["paths"]["/users"]["get"]["summary"] == "Get users from conflict_last"


def test_configure_openapi_merge_and_get_schema():
    # GIVEN a resolver
    app = APIGatewayRestResolver()

    # WHEN configuring openapi merge
    app.configure_openapi_merge(
        path=str(MERGE_HANDLERS_PATH),
        pattern="**/*_handler.py",
        exclude=["**/conflict_handler.py"],
        resolver_name="app",
        title="Resolver Merge API",
        version="1.0.0",
    )

    # THEN it should return merged schema
    schema = app.get_openapi_merge_schema()
    assert schema["info"]["title"] == "Resolver Merge API"
    assert "/users" in schema["paths"]
    assert "/orders" in schema["paths"]


def test_configure_openapi_merge_json_schema():
    # GIVEN a configured merge
    app = APIGatewayRestResolver()
    app.configure_openapi_merge(
        path=str(MERGE_HANDLERS_PATH),
        pattern="**/users_handler.py",
        title="JSON API",
        version="1.0.0",
    )

    # WHEN getting JSON schema
    json_schema = app.get_openapi_merge_json_schema()

    # THEN it should be valid JSON
    parsed = json.loads(json_schema)
    assert parsed["info"]["title"] == "JSON API"


def test_get_openapi_merge_schema_without_configure_raises():
    # GIVEN a resolver without configure_openapi_merge
    app = APIGatewayRestResolver()

    # WHEN/THEN should raise
    with pytest.raises(RuntimeError, match="configure_openapi_merge must be called"):
        app.get_openapi_merge_schema()


def test_get_openapi_merge_json_schema_without_configure_raises():
    # GIVEN a resolver without configure_openapi_merge
    app = APIGatewayRestResolver()

    # WHEN/THEN should raise
    with pytest.raises(RuntimeError, match="configure_openapi_merge must be called"):
        app.get_openapi_merge_json_schema()


def test_enable_swagger_uses_merged_schema():
    # GIVEN a resolver with configure_openapi_merge
    app = APIGatewayRestResolver()
    app.configure_openapi_merge(
        path=str(MERGE_HANDLERS_PATH),
        pattern="**/*_handler.py",
        exclude=["**/conflict_handler.py"],
        resolver_name="app",
        title="Swagger Merge API",
        version="2.0.0",
    )
    app.enable_swagger(path="/swagger")

    # WHEN calling swagger endpoint with format=json
    event = {
        "httpMethod": "GET",
        "path": "/swagger",
        "queryStringParameters": {"format": "json"},
        "headers": {},
        "requestContext": {"stage": "prod", "path": "/prod/swagger"},
    }
    response = app.resolve(event, {})

    # THEN it should return merged schema
    body = json.loads(response["body"])
    assert body["info"]["title"] == "Swagger Merge API"
    assert "/users" in body["paths"]
    assert "/orders" in body["paths"]


def test_enable_swagger_without_merge_uses_regular_schema():
    # GIVEN a resolver without configure_openapi_merge
    app = APIGatewayRestResolver()

    @app.get("/local")
    def local_endpoint():
        return {"local": True}

    app.enable_swagger(path="/swagger", title="Local API", version="1.0.0")

    # WHEN calling swagger endpoint
    event = {
        "httpMethod": "GET",
        "path": "/swagger",
        "queryStringParameters": {"format": "json"},
        "headers": {},
        "requestContext": {"stage": "prod", "path": "/prod/swagger"},
    }
    response = app.resolve(event, {})

    # THEN it should return local schema only
    body = json.loads(response["body"])
    assert body["info"]["title"] == "Local API"
    assert "/local" in body["paths"]
    assert "/users" not in body["paths"]
