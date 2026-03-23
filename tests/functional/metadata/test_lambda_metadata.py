"""Tests for Lambda Metadata Service utility."""

from __future__ import annotations

from collections import namedtuple
from unittest.mock import patch

import pytest

from aws_lambda_powertools.utilities.metadata import (
    LambdaMetadata,
    LambdaMetadataError,
    clear_metadata_cache,
    get_lambda_metadata,
)

MOCK_METADATA_RESPONSE = {"AvailabilityZoneID": "use1-az1"}


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


@pytest.fixture
def mock_metadata_endpoint(monkeypatch):
    """Simulate a Lambda environment with metadata env vars and mock the HTTP fetch."""
    monkeypatch.setenv("AWS_LAMBDA_INITIALIZATION_TYPE", "on-demand")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_API", "127.0.0.1:1234")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_TOKEN", "test-token")

    with patch(
        "aws_lambda_powertools.utilities.metadata.lambda_metadata._fetch_metadata",
        return_value=MOCK_METADATA_RESPONSE,
    ) as mock_fetch:
        yield mock_fetch


# ---------------------------------------------------------------------------
# LambdaMetadata dataclass
# ---------------------------------------------------------------------------


def test_lambda_metadata_default_has_none_az():
    # GIVEN no data
    # WHEN creating a default LambdaMetadata
    metadata = LambdaMetadata()

    # THEN availability_zone_id is None
    assert metadata.availability_zone_id is None


def test_lambda_metadata_is_frozen():
    # GIVEN a LambdaMetadata instance
    metadata = LambdaMetadata(availability_zone_id="use1-az1")

    # WHEN trying to mutate it
    # THEN it raises FrozenInstanceError
    with pytest.raises(AttributeError):
        metadata.availability_zone_id = "use1-az2"


# ---------------------------------------------------------------------------
# LambdaMetadataError
# ---------------------------------------------------------------------------


def test_lambda_metadata_error_defaults_status_code_to_minus_one():
    # GIVEN a message only
    # WHEN creating a LambdaMetadataError
    err = LambdaMetadataError("something broke")

    # THEN message is set and status_code defaults to -1
    assert str(err) == "something broke"
    assert err.status_code == -1


def test_lambda_metadata_error_stores_status_code():
    # GIVEN a message and a status code
    # WHEN creating a LambdaMetadataError
    err = LambdaMetadataError("not found", status_code=404)

    # THEN the status_code is stored
    assert err.status_code == 404


# ---------------------------------------------------------------------------
# get_lambda_metadata – non-Lambda / dev mode
# ---------------------------------------------------------------------------


def test_get_lambda_metadata_returns_empty_outside_lambda(lambda_context, lambda_event, monkeypatch):
    # GIVEN AWS_LAMBDA_INITIALIZATION_TYPE is not set (local dev / tests)
    monkeypatch.delenv("AWS_LAMBDA_INITIALIZATION_TYPE", raising=False)

    def handler(event, context):
        return get_lambda_metadata()

    # WHEN the handler is invoked
    result = handler(lambda_event, lambda_context)

    # THEN it returns empty metadata without calling the endpoint
    assert result.availability_zone_id is None


def test_get_lambda_metadata_returns_empty_when_dev_mode(lambda_context, lambda_event, monkeypatch):
    # GIVEN POWERTOOLS_DEV is enabled even though init type is set
    monkeypatch.setenv("POWERTOOLS_DEV", "true")
    monkeypatch.setenv("AWS_LAMBDA_INITIALIZATION_TYPE", "on-demand")

    def handler(event, context):
        return get_lambda_metadata()

    # WHEN the handler is invoked
    result = handler(lambda_event, lambda_context)

    # THEN it returns empty metadata
    assert result.availability_zone_id is None


# ---------------------------------------------------------------------------
# get_lambda_metadata – missing env vars
# ---------------------------------------------------------------------------


def test_get_lambda_metadata_raises_when_api_env_var_missing(lambda_context, lambda_event, monkeypatch):
    # GIVEN a Lambda environment without AWS_LAMBDA_METADATA_API
    monkeypatch.setenv("AWS_LAMBDA_INITIALIZATION_TYPE", "on-demand")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_TOKEN", "tok")
    monkeypatch.delenv("AWS_LAMBDA_METADATA_API", raising=False)

    def handler(event, context):
        return get_lambda_metadata()

    # WHEN the handler is invoked
    # THEN it raises LambdaMetadataError mentioning the missing var
    with pytest.raises(LambdaMetadataError, match="AWS_LAMBDA_METADATA_API"):
        handler(lambda_event, lambda_context)


def test_get_lambda_metadata_raises_when_token_env_var_missing(lambda_context, lambda_event, monkeypatch):
    # GIVEN a Lambda environment without AWS_LAMBDA_METADATA_TOKEN
    monkeypatch.setenv("AWS_LAMBDA_INITIALIZATION_TYPE", "on-demand")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_API", "127.0.0.1:9999")
    monkeypatch.delenv("AWS_LAMBDA_METADATA_TOKEN", raising=False)

    def handler(event, context):
        return get_lambda_metadata()

    # WHEN the handler is invoked
    # THEN it raises LambdaMetadataError mentioning the missing var
    with pytest.raises(LambdaMetadataError, match="AWS_LAMBDA_METADATA_TOKEN"):
        handler(lambda_event, lambda_context)


# ---------------------------------------------------------------------------
# get_lambda_metadata – happy path
# ---------------------------------------------------------------------------


def test_get_lambda_metadata_returns_az_id(lambda_context, lambda_event, mock_metadata_endpoint):
    # GIVEN a Lambda environment with metadata env vars configured
    def handler(event, context):
        return get_lambda_metadata()

    # WHEN the handler is invoked
    result = handler(lambda_event, lambda_context)

    # THEN it returns metadata with the availability zone id
    assert result.availability_zone_id == "use1-az1"
    mock_metadata_endpoint.assert_called_once()


def test_get_lambda_metadata_caches_across_invocations(lambda_context, lambda_event, mock_metadata_endpoint):
    # GIVEN a Lambda environment with metadata env vars configured
    def handler(event, context):
        return get_lambda_metadata()

    # WHEN the handler is invoked twice (simulating warm start)
    first = handler(lambda_event, lambda_context)
    second = handler(lambda_event, lambda_context)

    # THEN both return the same data and the endpoint was called only once
    assert first.availability_zone_id == "use1-az1"
    assert second.availability_zone_id == "use1-az1"
    mock_metadata_endpoint.assert_called_once()


def test_get_lambda_metadata_refetches_after_cache_clear(lambda_context, lambda_event, mock_metadata_endpoint):
    # GIVEN a Lambda environment with metadata env vars configured
    def handler(event, context):
        return get_lambda_metadata()

    # WHEN the handler is invoked, cache is cleared, then invoked again
    first = handler(lambda_event, lambda_context)
    clear_metadata_cache()
    second = handler(lambda_event, lambda_context)

    # THEN the endpoint was called twice (cache was invalidated)
    assert first.availability_zone_id == "use1-az1"
    assert second.availability_zone_id == "use1-az1"
    assert mock_metadata_endpoint.call_count == 2


# ---------------------------------------------------------------------------
# get_lambda_metadata – error responses
# ---------------------------------------------------------------------------


def test_get_lambda_metadata_raises_on_endpoint_error(lambda_context, lambda_event, monkeypatch):
    # GIVEN a Lambda environment where the endpoint returns a 500
    monkeypatch.setenv("AWS_LAMBDA_INITIALIZATION_TYPE", "on-demand")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_API", "127.0.0.1:1234")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_TOKEN", "test-token")

    def handler(event, context):
        return get_lambda_metadata()

    # WHEN the handler is invoked and the endpoint fails
    with patch(
        "aws_lambda_powertools.utilities.metadata.lambda_metadata._fetch_metadata",
        side_effect=LambdaMetadataError("Metadata request failed with status 500", status_code=500),
    ):
        # THEN it raises LambdaMetadataError with the status code
        with pytest.raises(LambdaMetadataError, match="status 500") as exc_info:
            handler(lambda_event, lambda_context)

        assert exc_info.value.status_code == 500
