"""DataclassSerializer must save results with non-JSON-native fields and rebuild them on replay."""

from __future__ import annotations

import dataclasses
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum

from aws_lambda_powertools.utilities.idempotency import IdempotencyConfig, idempotent_function
from aws_lambda_powertools.utilities.idempotency.exceptions import IdempotencyItemAlreadyExistsError
from aws_lambda_powertools.utilities.idempotency.persistence.base import BasePersistenceLayer, DataRecord
from aws_lambda_powertools.utilities.idempotency.serialization.dataclass import DataclassSerializer


class InMemoryPersistenceLayer(BasePersistenceLayer):
    """Stores the serialized record the way a real table would, so replay reads back what was saved."""

    def __init__(self):
        super().__init__()
        self.records: dict[str, DataRecord] = {}

    def _put_record(self, data_record: DataRecord) -> None:
        if data_record.idempotency_key in self.records:
            raise IdempotencyItemAlreadyExistsError
        self.records[data_record.idempotency_key] = data_record

    def _update_record(self, data_record: DataRecord) -> None:
        self.records[data_record.idempotency_key] = data_record

    def _get_record(self, idempotency_key) -> DataRecord:
        return self.records[idempotency_key]

    def _delete_record(self, data_record: DataRecord) -> None:
        self.records.pop(data_record.idempotency_key, None)


class FakeLambdaContext:
    def get_remaining_time_in_millis(self) -> int:
        return 1000


class Color(Enum):
    RED = "red"


@dataclasses.dataclass
class Item:
    sku: str
    shipped_on: date


@dataclasses.dataclass
class Order:
    id: uuid.UUID
    created: datetime
    item: Item
    items: list[Item]
    color: Color
    total: Decimal
    coupon: Item | None = None
    by_name: dict[str, Item] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class Receipt:
    number: str
    note: str | None = None


def _build_order() -> Order:
    return Order(
        id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        created=datetime(2026, 1, 1, 10, 30, tzinfo=timezone.utc),
        item=Item(sku="a", shipped_on=date(2026, 1, 2)),
        items=[Item(sku="b", shipped_on=date(2026, 1, 3))],
        color=Color.RED,
        total=Decimal("19.90"),
        coupon=Item(sku="c", shipped_on=date(2026, 1, 4)),
        by_name={"k": Item(sku="d", shipped_on=date(2026, 1, 5))},
    )


def _decorate(function, persistence_layer):
    config = IdempotencyConfig(use_local_cache=False)
    config.register_lambda_context(FakeLambdaContext())
    return idempotent_function(
        function,
        data_keyword_argument="order",
        persistence_store=persistence_layer,
        config=config,
        output_serializer=DataclassSerializer,
    )


def test_dataclass_serializer_saves_and_replays_non_json_native_fields():
    # GIVEN a function returning a dataclass with UUID, datetime, date, Enum, Decimal and nested dataclasses
    calls = []

    def process(order: dict) -> Order:
        calls.append(order)
        return _build_order()

    persistence_layer = InMemoryPersistenceLayer()
    decorated = _decorate(process, persistence_layer)

    # WHEN the same payload is sent twice
    first = decorated(order={"id": 1})
    second = decorated(order={"id": 1})

    # THEN the first result is saved as COMPLETED instead of raising
    assert [record.status for record in persistence_layer.records.values()] == ["COMPLETED"]

    # AND the second call replays the stored result without running the function again
    assert len(calls) == 1

    # AND the replayed value equals the original, nested dataclasses included
    assert first == _build_order()
    assert second == first
    assert isinstance(second.item, Item)
    assert isinstance(second.items[0], Item)
    assert isinstance(second.coupon, Item)
    assert isinstance(second.by_name["k"], Item)


def test_dataclass_serializer_replays_plain_string_fields_unchanged():
    # GIVEN a dataclass with only plain fields, as before this change
    def process(order: dict) -> Receipt:
        return Receipt(number="42", note="2026-01-01")

    decorated = _decorate(process, InMemoryPersistenceLayer())

    # WHEN it is replayed
    first = decorated(order={"id": 1})
    second = decorated(order={"id": 1})

    # THEN string values that merely look like dates are not converted
    assert first == second == Receipt(number="42", note="2026-01-01")
