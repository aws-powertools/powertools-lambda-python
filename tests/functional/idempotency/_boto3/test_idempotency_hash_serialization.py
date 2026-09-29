import dataclasses
import datetime
from decimal import Decimal
from enum import Enum, IntEnum
from pathlib import PurePosixPath
from typing import Any, NamedTuple

import pytest
from botocore import stub
from jmespath import functions

from aws_lambda_powertools.utilities.idempotency import IdempotencyConfig, idempotent_function
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyPersistenceLayerError,
    IdempotencyValidationError,
)
from tests.functional.idempotency.utils import (
    build_idempotency_put_item_stub,
    build_idempotency_update_item_stub,
    hash_idempotency_key,
)
from tests.functional.utils import json_serialize


@dataclasses.dataclass
class Payload:
    order_id: str
    value: Any


class DecimalAmount(Decimal, Enum):
    SMALL = Decimal("1.00")


class StringStatus(str, Enum):
    PAID = "paid"


class IntegerStatus(IntEnum):
    PAID = 1


class FloatStatus(float, Enum):
    PAID = 1.5


class Point(NamedTuple):
    x: int
    y: int


def _expected_put(key_data, validation_data):
    params = build_idempotency_put_item_stub(key_data)
    params["Item"]["id"] = {"S": f"orders#{hash_idempotency_key(key_data)}"}
    params["Item"]["validation"] = {"S": hash_idempotency_key(validation_data)}
    return params


def _completed_record(key_data, validation_data, expiration):
    return {
        "Item": {
            "id": {"S": f"orders#{hash_idempotency_key(key_data)}"},
            "expiration": {"N": expiration},
            "status": {"S": "COMPLETED"},
            "data": {"S": json_serialize({"status": "already processed"})},
            "validation": {"S": hash_idempotency_key(validation_data)},
        },
    }


def _assert_existing_record_is_reused(store, config, payload, key_data, validation_data, expiration):
    @idempotent_function(
        data_keyword_argument="payload",
        persistence_store=store,
        config=config,
        key_prefix="orders",
    )
    def process(payload):
        pytest.fail("An existing record must be reused without executing the function")

    # Both hashes are produced by the existing shared Encoder, independently of the new hash encoder.
    with stub.Stubber(store.client) as stubber:
        stubber.add_client_error(
            "put_item",
            "ConditionalCheckFailedException",
            modeled_fields=_completed_record(key_data, validation_data, expiration),
            expected_params=_expected_put(key_data, validation_data),
        )
        assert process(payload=payload) == {"status": "already processed"}
        stubber.assert_no_pending_responses()


@pytest.mark.parametrize("as_dataclass", [True, False], ids=["dataclass", "dict"])
@pytest.mark.parametrize(
    "value",
    [
        pytest.param({"text": "café", "integer": 1, "float": 1.5, "bool": True, "null": None}, id="primitives"),
        pytest.param(Decimal("1.00"), id="decimal"),
        pytest.param(Decimal("NaN"), id="decimal-nan"),
        pytest.param(DecimalAmount.SMALL, id="decimal-enum"),
        pytest.param(StringStatus.PAID, id="str-enum"),
        pytest.param(IntegerStatus.PAID, id="int-enum"),
        pytest.param(FloatStatus.PAID, id="float-enum"),
        pytest.param((1, "two", Decimal("3.00")), id="tuple"),
        pytest.param(Point(1, 2), id="namedtuple"),
        pytest.param(Payload("nested", Decimal("1.00")), id="nested-dataclass"),
    ],
)
def test_existing_key_and_validation_hashes_are_preserved(
    persistence_store,
    lambda_context,
    timestamp_future,
    as_dataclass,
    value,
):
    payload = Payload("order-1", value)
    legacy_data = dataclasses.asdict(payload)
    config = IdempotencyConfig(payload_validation_jmespath="value", lambda_context=lambda_context)

    _assert_existing_record_is_reused(
        persistence_store,
        config,
        payload if as_dataclass else legacy_data,
        legacy_data,
        legacy_data["value"],
        timestamp_future,
    )


@pytest.mark.parametrize(
    "value,expected_type",
    [
        pytest.param(datetime.datetime(2024, 3, 20, 14, 30), None, id="datetime"),
        pytest.param(DecimalAmount.SMALL, None, id="decimal-enum"),
        pytest.param(Point(1, 2), None, id="namedtuple"),
        pytest.param([1, 2], "array", id="list"),
    ],
)
@pytest.mark.parametrize("custom_function", [False, True], ids=["builtin", "custom"])
def test_jmespath_sees_original_types_before_hashing(
    persistence_store,
    lambda_context,
    timestamp_future,
    value,
    expected_type,
    custom_function,
):
    class CustomFunctions(functions.Functions):
        @functions.signature({"types": []})
        def _func_original_type(self, value):
            return type(value).__name__

    if custom_function:
        expression = "original_type(value)"
        expected_type = type(value).__name__
    else:
        expression = "type(value)"

    key_data = {"order": "order-1", "kind": expected_type}
    validation_data = {"kind": expected_type}
    config = IdempotencyConfig(
        event_key_jmespath=f"{{order: order_id, kind: {expression}}}",
        payload_validation_jmespath=f"{{kind: {expression}}}",
        jmespath_options={"custom_functions": CustomFunctions()},
        lambda_context=lambda_context,
    )
    _assert_existing_record_is_reused(
        persistence_store,
        config,
        Payload("order-1", value),
        key_data,
        validation_data,
        timestamp_future,
    )


@pytest.mark.parametrize("as_dataclass", [True, False], ids=["dataclass", "dict"])
def test_new_types_support_persistent_replay_and_payload_validation(
    persistence_store,
    lambda_context,
    timestamp_future,
    as_dataclass,
):
    value = datetime.datetime(2024, 3, 20, 14, 30, tzinfo=datetime.timezone.utc)
    payload = Payload("order-1", {"created_at": value, "receipt": PurePosixPath("/orders/receipt.pdf")})
    prepared_value = {"created_at": value.isoformat(), "receipt": "/orders/receipt.pdf"}
    config = IdempotencyConfig(
        event_key_jmespath="order_id",
        payload_validation_jmespath="value",
        lambda_context=lambda_context,
        use_local_cache=False,
    )
    executions = []

    @idempotent_function(
        data_keyword_argument="payload",
        persistence_store=persistence_store,
        config=config,
        key_prefix="orders",
    )
    def process(payload):
        executions.append(payload)
        return {"status": "already processed"}

    expected_update = build_idempotency_update_item_stub("order-1", {"status": "already processed"})
    expected_update["Key"]["id"] = {"S": f"orders#{hash_idempotency_key('order-1')}"}
    expected_update["ExpressionAttributeNames"]["#validation_key"] = "validation"
    expected_update["ExpressionAttributeValues"][":validation_key"] = {"S": hash_idempotency_key(prepared_value)}
    expected_update["UpdateExpression"] += ", #validation_key = :validation_key"

    with stub.Stubber(persistence_store.client) as stubber:
        stubber.add_response("put_item", {}, _expected_put("order-1", prepared_value))
        stubber.add_response("update_item", {}, expected_update)
        stubber.add_client_error(
            "put_item",
            "ConditionalCheckFailedException",
            modeled_fields=_completed_record("order-1", prepared_value, timestamp_future),
            expected_params=_expected_put("order-1", prepared_value),
        )

        request = payload if as_dataclass else dataclasses.asdict(payload)
        assert process(payload=request) == {"status": "already processed"}
        assert process(payload=request) == {"status": "already processed"}
        assert len(executions) == 1

        changed = dataclasses.replace(payload, value={**payload.value, "receipt": PurePosixPath("/other.pdf")})
        changed_value = {**prepared_value, "receipt": "/other.pdf"}
        stubber.add_client_error(
            "put_item",
            "ConditionalCheckFailedException",
            modeled_fields=_completed_record("order-1", prepared_value, timestamp_future),
            expected_params=_expected_put("order-1", changed_value),
        )
        with pytest.raises(IdempotencyValidationError):
            process(payload=changed if as_dataclass else dataclasses.asdict(changed))

        assert len(executions) == 1
        stubber.assert_no_pending_responses()


@pytest.mark.parametrize("value", [b"bytes", {1, 2}, complex(1, 2)], ids=["bytes", "set", "complex"])
def test_unsupported_key_types_still_raise(persistence_store, lambda_context, value):
    @idempotent_function(
        data_keyword_argument="payload",
        persistence_store=persistence_store,
        config=IdempotencyConfig(lambda_context=lambda_context),
    )
    def process(payload):
        pytest.fail("Unsupported key types must fail before executing the function")

    with stub.Stubber(persistence_store.client) as stubber:
        with pytest.raises(IdempotencyPersistenceLayerError) as error:
            process(payload=Payload("order-1", value))
        assert isinstance(error.value.__cause__, TypeError)
        assert "is not JSON serializable" in str(error.value.__cause__)
        stubber.assert_no_pending_responses()
