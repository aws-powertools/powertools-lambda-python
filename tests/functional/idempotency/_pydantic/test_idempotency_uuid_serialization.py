"""
Test for issue #8065: @idempotent_function fails with UUID in Pydantic model

Bug: _prepare_data() calls model_dump() without mode="json", which doesn't
serialize UUIDs and dates to JSON-compatible strings.
"""

from datetime import date, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel

from aws_lambda_powertools.utilities.idempotency import (
    IdempotencyConfig,
    idempotent_function,
)
from aws_lambda_powertools.utilities.idempotency.base import _prepare_data
from aws_lambda_powertools.utilities.idempotency.persistence.base import (
    BasePersistenceLayer,
    DataRecord,
)
from tests.functional.idempotency.utils import hash_idempotency_key


TESTS_MODULE_PREFIX = "test-func.tests.functional.idempotency._pydantic.test_idempotency_uuid_serialization"


class MockPersistenceLayer(BasePersistenceLayer):
    """Mock persistence layer that tracks idempotency key assertions."""

    def __init__(self, expected_idempotency_key: str):
        self.expected_idempotency_key = expected_idempotency_key
        super().__init__()

    def _put_record(self, data_record: DataRecord) -> None:
        assert data_record.idempotency_key == self.expected_idempotency_key

    def _update_record(self, data_record: DataRecord) -> None:
        assert data_record.idempotency_key == self.expected_idempotency_key

    def _get_record(self, idempotency_key) -> DataRecord:
        ...

    def _delete_record(self, data_record: DataRecord) -> None:
        ...


class PaymentWithUUID(BaseModel):
    """Pydantic model with UUID field - reproduces issue #8065."""

    payment_id: UUID
    customer_id: str


class EventWithDate(BaseModel):
    """Pydantic model with date field."""

    event_id: str
    event_date: date


class OrderWithDatetime(BaseModel):
    """Pydantic model with datetime field."""

    order_id: str
    created_at: datetime


def test_prepare_data_pydantic_with_uuid():
    """
    Test that _prepare_data correctly serializes Pydantic models with UUID fields.

    Issue #8065: model_dump() without mode="json" returns UUID objects instead of strings,
    which causes "Object of type UUID is not JSON serializable" error.
    """
    # GIVEN a Pydantic model with UUID
    payment_uuid = uuid4()
    payment = PaymentWithUUID(payment_id=payment_uuid, customer_id="customer-123")

    # WHEN preparing data for idempotency
    result = _prepare_data(payment)

    # THEN UUID should be serialized as string (not UUID object)
    assert isinstance(result, dict)
    assert isinstance(result["payment_id"], str), (
        f"UUID should be serialized as string, got {type(result['payment_id'])}"
    )
    assert result["payment_id"] == str(payment_uuid)
    assert result["customer_id"] == "customer-123"


def test_prepare_data_pydantic_with_date():
    """Test that _prepare_data correctly serializes Pydantic models with date fields."""
    # GIVEN a Pydantic model with date
    event_date = date(2024, 1, 15)
    event = EventWithDate(event_id="event-123", event_date=event_date)

    # WHEN preparing data for idempotency
    result = _prepare_data(event)

    # THEN date should be serialized as ISO format string
    assert isinstance(result, dict)
    assert isinstance(result["event_date"], str), (
        f"date should be serialized as string, got {type(result['event_date'])}"
    )
    assert result["event_date"] == "2024-01-15"


def test_prepare_data_pydantic_with_datetime():
    """Test that _prepare_data correctly serializes Pydantic models with datetime fields."""
    # GIVEN a Pydantic model with datetime
    created_at = datetime(2024, 1, 15, 10, 30, 0)
    order = OrderWithDatetime(order_id="order-123", created_at=created_at)

    # WHEN preparing data for idempotency
    result = _prepare_data(order)

    # THEN datetime should be serialized as ISO format string
    assert isinstance(result, dict)
    assert isinstance(result["created_at"], str), (
        f"datetime should be serialized as string, got {type(result['created_at'])}"
    )


def test_idempotent_function_with_uuid_in_pydantic_model():
    """
    Integration test for idempotent_function with UUID in Pydantic model.

    This is the main test case for issue #8065.
    """
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    payment_uuid = UUID("12345678-1234-5678-1234-567812345678")
    mock_event = {"payment_id": str(payment_uuid), "customer_id": "customer-456"}

    idempotency_key = (
        f"{TESTS_MODULE_PREFIX}.test_idempotent_function_with_uuid_in_pydantic_model"
        f".<locals>.process_payment#{hash_idempotency_key(mock_event)}"
    )
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    @idempotent_function(
        data_keyword_argument="payment",
        persistence_store=persistence_layer,
        config=config,
    )
    def process_payment(payment: PaymentWithUUID) -> dict:
        return {"status": "processed", "payment_id": str(payment.payment_id)}

    # WHEN processing payment with UUID
    payment = PaymentWithUUID(payment_id=payment_uuid, customer_id="customer-456")

    # THEN it should not raise "Object of type UUID is not JSON serializable"
    result = process_payment(payment=payment)
    assert result["status"] == "processed"
    assert result["payment_id"] == str(payment_uuid)
