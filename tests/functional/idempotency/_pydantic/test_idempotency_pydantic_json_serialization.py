"""
Test for issue #8065: @idempotent_function fails with non-JSON-serializable types in Pydantic models

Bug: _prepare_data() calls model_dump() without mode="json", which doesn't
serialize UUIDs, dates, datetimes, Decimals, and Paths to JSON-compatible strings.
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import PurePosixPath
from uuid import UUID

from pydantic import BaseModel

from aws_lambda_powertools.utilities.idempotency import (
    IdempotencyConfig,
    idempotent_function,
)
from aws_lambda_powertools.utilities.idempotency.persistence.base import (
    BasePersistenceLayer,
    DataRecord,
)
from tests.functional.idempotency.utils import hash_idempotency_key

TESTS_MODULE_PREFIX = "test-func.tests.functional.idempotency._pydantic.test_idempotency_pydantic_json_serialization"


class MockPersistenceLayer(BasePersistenceLayer):
    def __init__(self, expected_idempotency_key: str):
        self.expected_idempotency_key = expected_idempotency_key
        super().__init__()

    def _put_record(self, data_record: DataRecord) -> None:
        assert data_record.idempotency_key == self.expected_idempotency_key

    def _update_record(self, data_record: DataRecord) -> None:
        assert data_record.idempotency_key == self.expected_idempotency_key

    def _get_record(self, idempotency_key) -> DataRecord: ...

    def _delete_record(self, data_record: DataRecord) -> None: ...


# --- Models ---


class PaymentWithUUID(BaseModel):
    payment_id: UUID
    customer_id: str


class EventWithDate(BaseModel):
    event_id: str
    event_date: date


class OrderWithDatetime(BaseModel):
    order_id: str
    created_at: datetime


class InvoiceWithDecimal(BaseModel):
    invoice_id: str
    amount: Decimal


class ConfigWithPath(BaseModel):
    config_id: str
    file_path: PurePosixPath


def test_idempotent_function_with_uuid():
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    payment_uuid = UUID("12345678-1234-5678-1234-567812345678")
    mock_event = {"payment_id": str(payment_uuid), "customer_id": "c-456"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_with_uuid.<locals>.collect_payment#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    @idempotent_function(
        data_keyword_argument="payment",
        persistence_store=persistence_layer,
        config=config,
    )
    def collect_payment(payment: PaymentWithUUID) -> dict:
        return {"status": "ok"}

    # WHEN
    payment = PaymentWithUUID(payment_id=payment_uuid, customer_id="c-456")
    result = collect_payment(payment=payment)

    # THEN
    assert result == {"status": "ok"}


def test_idempotent_function_with_date():
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"event_id": "evt-001", "event_date": "2024-03-20"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_with_date.<locals>.process_event#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    @idempotent_function(
        data_keyword_argument="event",
        persistence_store=persistence_layer,
        config=config,
    )
    def process_event(event: EventWithDate) -> dict:
        return {"status": "ok"}

    # WHEN
    event = EventWithDate(event_id="evt-001", event_date=date(2024, 3, 20))
    result = process_event(event=event)

    # THEN
    assert result == {"status": "ok"}


def test_idempotent_function_with_datetime():
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"order_id": "ord-001", "created_at": "2024-03-20T14:30:00"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_with_datetime.<locals>.process_order#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    @idempotent_function(
        data_keyword_argument="order",
        persistence_store=persistence_layer,
        config=config,
    )
    def process_order(order: OrderWithDatetime) -> dict:
        return {"status": "ok"}

    # WHEN
    order = OrderWithDatetime(order_id="ord-001", created_at=datetime(2024, 3, 20, 14, 30, 0))
    result = process_order(order=order)

    # THEN
    assert result == {"status": "ok"}


def test_idempotent_function_with_decimal():
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"invoice_id": "inv-001", "amount": "199.99"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_with_decimal.<locals>.process_invoice#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    @idempotent_function(
        data_keyword_argument="invoice",
        persistence_store=persistence_layer,
        config=config,
    )
    def process_invoice(invoice: InvoiceWithDecimal) -> dict:
        return {"status": "ok"}

    # WHEN
    invoice = InvoiceWithDecimal(invoice_id="inv-001", amount=Decimal("199.99"))
    result = process_invoice(invoice=invoice)

    # THEN
    assert result == {"status": "ok"}


def test_idempotent_function_with_path():
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"config_id": "cfg-001", "file_path": "/etc/app/config.yaml"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_with_path.<locals>.process_config#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    @idempotent_function(
        data_keyword_argument="config",
        persistence_store=persistence_layer,
        config=config,
    )
    def process_config(config: ConfigWithPath) -> dict:
        return {"status": "ok"}

    # WHEN
    cfg = ConfigWithPath(config_id="cfg-001", file_path=PurePosixPath("/etc/app/config.yaml"))
    result = process_config(config=cfg)

    # THEN
    assert result == {"status": "ok"}
