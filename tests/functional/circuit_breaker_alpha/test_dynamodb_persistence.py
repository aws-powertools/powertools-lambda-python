from __future__ import annotations

import boto3
import pytest
from botocore.config import Config
from botocore.stub import Stubber

from aws_lambda_powertools.utilities.circuit_breaker_alpha.config import CircuitBreakerConfig
from aws_lambda_powertools.utilities.circuit_breaker_alpha.exceptions import CircuitBreakerConfigError
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence import (
    CircuitBreakerDynamoDBPersistence,
)
from aws_lambda_powertools.utilities.circuit_breaker_alpha.states import CircuitState
from aws_lambda_powertools.warnings import PowertoolsUserWarning

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
    # Condition supports both fresh election (OPEN, no owner, matching opened_at) and
    # lease takeover (HALF_OPEN with expired lease).
    assert "#state = :open AND attribute_not_exists(#half_open_owner)" in captured["ConditionExpression"]
    assert "#probe_lease_expiry <= :now" in captured["ConditionExpression"]
    assert captured["ExpressionAttributeValues"][":open"] == {"S": "OPEN"}
    assert captured["ExpressionAttributeValues"][":expected_opened_at"] == {"N": "1000"}
    assert "probe_lease_expiry" in item


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


# --------------------------------------------------------------------------- serialization coverage


def test_item_to_record_full_item(persistence):
    """Cover _item_to_record with all fields present (lines 109-122)."""
    item = {
        "id": {"S": "payment"},
        "state": {"S": "HALF_OPEN"},
        "failure_count": {"N": "3"},
        "opened_at": {"N": "1000"},
        "half_open_owner": {"S": "env-x"},
        "probe_lease_expiry": {"N": "2000"},
        "expiration": {"N": "9999"},
    }
    record = persistence._item_to_record(item)
    assert record.name == "payment"
    assert record.state == CircuitState.HALF_OPEN
    assert record.failure_count == 3
    assert record.opened_at == 1000
    assert record.half_open_owner == "env-x"
    assert record.probe_lease_expiry == 2000
    assert record.expiry_timestamp == 9999


def test_item_to_record_minimal_item(persistence):
    """Cover _item_to_record with optional fields absent."""
    item = {
        "id": {"S": "payment"},
        "state": {"S": "CLOSED"},
    }
    record = persistence._item_to_record(item)
    assert record.name == "payment"
    assert record.state == CircuitState.CLOSED
    assert record.failure_count == 0
    assert record.opened_at is None
    assert record.half_open_owner is None
    assert record.probe_lease_expiry is None


def test_record_to_item_full_record(persistence):
    """Cover _record_to_item with all fields set (lines 124-139)."""
    from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence.record import CircuitStateRecord

    record = CircuitStateRecord(
        name="payment",
        state=CircuitState.HALF_OPEN,
        failure_count=5,
        opened_at=1000,
        half_open_owner="env-a",
        probe_lease_expiry=2000,
        expiry_timestamp=9999,
    )
    item = persistence._record_to_item(record)
    assert item["id"] == {"S": "payment"}
    assert item["state"] == {"S": "HALF_OPEN"}
    assert item["failure_count"] == {"N": "5"}
    assert item["opened_at"] == {"N": "1000"}
    assert item["half_open_owner"] == {"S": "env-a"}
    assert item["probe_lease_expiry"] == {"N": "2000"}
    assert item["expiration"] == {"N": "9999"}


def test_record_to_item_minimal_record(persistence):
    """Cover _record_to_item with optional fields as None (branch misses on lines 131-137)."""
    from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence.record import CircuitStateRecord

    record = CircuitStateRecord(name="payment", state=CircuitState.CLOSED)
    item = persistence._record_to_item(record)
    assert item == {
        "id": {"S": "payment"},
        "state": {"S": "CLOSED"},
        "failure_count": {"N": "0"},
    }
    assert "opened_at" not in item
    assert "half_open_owner" not in item
    assert "probe_lease_expiry" not in item
    assert "expiration" not in item


def test_get_record_returns_deserialized_item(persistence):
    """Cover _get_record success path (lines 141-153)."""
    stubber = Stubber(persistence.client)
    stubber.add_response(
        "get_item",
        {
            "Item": {
                "id": {"S": "payment"},
                "state": {"S": "OPEN"},
                "failure_count": {"N": "5"},
                "opened_at": {"N": "1000"},
            },
        },
        {"TableName": TABLE_NAME, "Key": {"id": {"S": "payment"}}, "ConsistentRead": False},
    )
    with stubber:
        record = persistence._get_record("payment")
    assert record.state == CircuitState.OPEN
    assert record.failure_count == 5
    assert record.opened_at == 1000


def test_build_half_open_condition_without_expected_opened_at(persistence):
    """Cover _build_half_open_condition when expected_opened_at is None (line 172 branch)."""
    result = persistence._build_half_open_condition(expected_opened_at=None)
    assert ":expected_opened_at" not in result["ConditionExpression"]
    assert "#opened_at" not in result["ExpressionAttributeNames"]


def test_build_half_open_condition_with_expected_opened_at(persistence):
    """Cover _build_half_open_condition when expected_opened_at is set (lines 172-177)."""
    result = persistence._build_half_open_condition(expected_opened_at=5000)
    assert "#opened_at = :expected_opened_at" in result["ConditionExpression"]
    assert result["ExpressionAttributeNames"]["#opened_at"] == "opened_at"
    assert result["ExpressionAttributeValues"][":expected_opened_at"] == {"N": "5000"}


# --------------------------------------------------------------------------- composite (single-table) key


COMPOSITE_KEY = {"PK": {"S": "CIRCUIT_BREAKER"}, "SK": {"S": "payment"}}


@pytest.fixture
def composite_persistence():
    client = boto3.client("dynamodb", config=Config(region_name="us-east-1"))
    layer = CircuitBreakerDynamoDBPersistence(
        table_name=TABLE_NAME,
        boto3_client=client,
        key_attr="PK",
        sort_key_attr="SK",
        static_pk_value="CIRCUIT_BREAKER",
    )
    layer.configure(CircuitBreakerConfig(local_cache_max_age=0), circuit_name="payment")
    return layer


def test_composite_get_state_reads_composite_key(composite_persistence):
    stubber = Stubber(composite_persistence.client)
    stubber.add_response(
        "get_item",
        {},
        {"TableName": TABLE_NAME, "Key": COMPOSITE_KEY, "ConsistentRead": False},
    )
    with stubber:
        record = composite_persistence.get_state("payment")
    assert record.state == CircuitState.CLOSED


def test_composite_save_open_writes_composite_key(composite_persistence):
    captured, restore = _capture_put_item(composite_persistence)
    try:
        composite_persistence.save_open("payment", failure_count=5, opened_at=1000)
    finally:
        restore()

    item = captured["Item"]
    assert item["PK"] == {"S": "CIRCUIT_BREAKER"}
    assert item["SK"] == {"S": "payment"}
    assert "id" not in item
    assert item["state"] == {"S": "OPEN"}


def test_composite_try_acquire_half_open_writes_composite_key(composite_persistence):
    captured, restore = _capture_put_item(composite_persistence)
    try:
        assert composite_persistence.try_acquire_half_open("payment", "env-a", 1000) is True
    finally:
        restore()

    item = captured["Item"]
    assert item["PK"] == {"S": "CIRCUIT_BREAKER"}
    assert item["SK"] == {"S": "payment"}
    assert item["state"] == {"S": "HALF_OPEN"}
    # The conditional election is still emitted in composite mode (condition is key-independent).
    assert "#state = :open AND attribute_not_exists(#half_open_owner)" in captured["ConditionExpression"]
    assert "#probe_lease_expiry <= :now" in captured["ConditionExpression"]


def test_composite_try_acquire_half_open_loses_on_conditional_failure(composite_persistence):
    stubber = Stubber(composite_persistence.client)
    stubber.add_client_error("put_item", service_error_code="ConditionalCheckFailedException")
    with stubber:
        assert composite_persistence.try_acquire_half_open("payment", "env-b", 1000) is False


def test_composite_save_closed_updates_composite_key(composite_persistence):
    captured = {}
    original_update = composite_persistence.client.update_item

    def capturing_update(**kwargs):
        captured.update(kwargs)
        return {}

    composite_persistence.client.update_item = capturing_update
    try:
        composite_persistence.save_closed("payment")
    finally:
        composite_persistence.client.update_item = original_update

    assert captured["Key"] == COMPOSITE_KEY


def test_composite_item_to_record_reads_name_from_sort_key(composite_persistence):
    item = {
        "PK": {"S": "CIRCUIT_BREAKER"},
        "SK": {"S": "payment"},
        "state": {"S": "OPEN"},
        "failure_count": {"N": "2"},
    }
    record = composite_persistence._item_to_record(item)
    assert record.name == "payment"
    assert record.state == CircuitState.OPEN


def test_sort_key_equal_to_key_attr_raises():
    client = boto3.client("dynamodb", config=Config(region_name="us-east-1"))
    with pytest.raises(CircuitBreakerConfigError, match="cannot be the same"):
        CircuitBreakerDynamoDBPersistence(
            table_name=TABLE_NAME,
            boto3_client=client,
            key_attr="PK",
            sort_key_attr="PK",
        )


def test_default_static_pk_value_namespaces_function_name(monkeypatch):
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "orders-fn")
    client = boto3.client("dynamodb", config=Config(region_name="us-east-1"))
    layer = CircuitBreakerDynamoDBPersistence(table_name=TABLE_NAME, boto3_client=client, sort_key_attr="SK")
    assert layer.static_pk_value == "circuit_breaker#orders-fn"


def test_static_pk_value_without_sort_key_attr_warns():
    client = boto3.client("dynamodb", config=Config(region_name="us-east-1"))
    with pytest.warns(PowertoolsUserWarning, match="static_pk_value is ignored unless sort_key_attr"):
        CircuitBreakerDynamoDBPersistence(
            table_name=TABLE_NAME,
            boto3_client=client,
            static_pk_value="CIRCUIT_BREAKER",
        )
