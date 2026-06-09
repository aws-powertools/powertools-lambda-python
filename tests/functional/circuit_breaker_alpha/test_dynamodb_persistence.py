from __future__ import annotations

import boto3
import pytest
from botocore.config import Config
from botocore.stub import Stubber

from aws_lambda_powertools.utilities.circuit_breaker_alpha.config import CircuitBreakerConfig
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence import (
    CircuitBreakerDynamoDBPersistence,
)
from aws_lambda_powertools.utilities.circuit_breaker_alpha.states import CircuitState

TABLE_NAME = "CircuitBreakerState"


@pytest.fixture
def persistence():
    client = boto3.client("dynamodb", config=Config(region_name="us-east-1"))
    layer = CircuitBreakerDynamoDBPersistence(table_name=TABLE_NAME, boto3_client=client)
    layer.configure(CircuitBreakerConfig(local_cache_max_age=0), circuit_name="payment")
    return layer


def test_get_state_missing_item_returns_closed(persistence):
    stubber = Stubber(persistence.client)
    stubber.add_response(
        "get_item",
        {},
        {"TableName": TABLE_NAME, "Key": {"id": {"S": "payment"}}, "ConsistentRead": False},
    )
    with stubber:
        record = persistence.get_state("payment")
    assert record.state == CircuitState.CLOSED


def test_get_state_failing_store_fails_open(persistence):
    stubber = Stubber(persistence.client)
    stubber.add_client_error("get_item", service_error_code="InternalServerError")
    with stubber:
        record = persistence.get_state("payment")
    assert record.state == CircuitState.CLOSED, "store failure must fail open (CLOSED)"


def _capture_put_item(persistence):
    """Patch put_item to capture its params instead of asserting a time-dependent TTL."""
    captured = {}
    original = persistence.client.put_item

    def capturing(**kwargs):
        captured.update(kwargs)
        return {}

    persistence.client.put_item = capturing
    return captured, lambda: setattr(persistence.client, "put_item", original)


def test_save_open_writes_open_item(persistence):
    captured, restore = _capture_put_item(persistence)
    try:
        persistence.save_open("payment", failure_count=5, opened_at=1000)
    finally:
        restore()

    item = captured["Item"]
    assert item["id"] == {"S": "payment"}
    assert item["state"] == {"S": "OPEN"}
    assert item["failure_count"] == {"N": "5"}
    assert item["opened_at"] == {"N": "1000"}
    assert "expiration" in item, "open item must carry a TTL"


def test_try_acquire_half_open_wins(persistence):
    captured, restore = _capture_put_item(persistence)
    try:
        assert persistence.try_acquire_half_open("payment", "env-a", 1000) is True
    finally:
        restore()

    item = captured["Item"]
    assert item["state"] == {"S": "HALF_OPEN"}
    assert item["half_open_owner"] == {"S": "env-a"}
    assert item["opened_at"] == {"N": "1000"}
    assert "expiration" in item
    assert captured["ConditionExpression"] == "#state = :open AND attribute_not_exists(#half_open_owner)"
    assert captured["ExpressionAttributeValues"] == {":open": {"S": "OPEN"}}


def test_try_acquire_half_open_loses_on_conditional_failure(persistence):
    stubber = Stubber(persistence.client)
    stubber.add_client_error("put_item", service_error_code="ConditionalCheckFailedException")
    with stubber:
        assert persistence.try_acquire_half_open("payment", "env-b", 1000) is False


def test_save_closed_updates_record(persistence):
    stubber = Stubber(persistence.client)
    stubber.add_response("update_item", {})
    with stubber:
        persistence.save_closed("payment")
    stubber.assert_no_pending_responses()


# --------------------------------------------------------------------------- bug regressions


def test_save_reopen_removes_half_open_owner(persistence):
    # Bug #1: HALF_OPEN -> OPEN must clear half_open_owner, otherwise the next
    # probe election (attribute_not_exists(half_open_owner)) can never succeed.
    captured = {}
    original_update = persistence.client.update_item

    def capturing_update(**kwargs):
        captured.update(kwargs)
        return {}

    persistence.client.update_item = capturing_update
    try:
        persistence.save_reopen("payment", opened_at=2000)
    finally:
        persistence.client.update_item = original_update

    expression = captured["UpdateExpression"]
    assert "REMOVE" in expression
    assert captured["ExpressionAttributeNames"]["#half_open_owner"] == "half_open_owner"
    assert "#half_open_owner" in expression.split("REMOVE", 1)[1], "owner must be in the REMOVE clause"


def test_save_open_item_contains_expiration_attribute(persistence):
    # Bug #2: the written item must carry the TTL (expiration) attribute, otherwise
    # the documented self-cleaning of abandoned circuits never happens. Capture the
    # actual PutItem params rather than asserting an exact (time-dependent) value.
    captured = {}
    persistence.local_cache_max_age = 5

    original_put = persistence.client.put_item

    def capturing_put(**kwargs):
        captured.update(kwargs)
        return {}

    persistence.client.put_item = capturing_put
    try:
        persistence.save_open("payment", failure_count=5, opened_at=1000)
    finally:
        persistence.client.put_item = original_put

    item = captured["Item"]
    assert "expiration" in item, "open item must carry a DynamoDB TTL attribute"
