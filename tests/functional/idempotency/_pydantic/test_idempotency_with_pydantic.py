import json
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

import pytest
from pydantic import BaseModel
from pytest_mock import MockerFixture

from aws_lambda_powertools.utilities.idempotency import (
    IdempotencyConfig,
    idempotent_function,
)
from aws_lambda_powertools.utilities.idempotency.base import (
    _prepare_data,
)
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyModelTypeError,
    IdempotencyNoSerializationModelError,
)
from aws_lambda_powertools.utilities.idempotency.persistence.base import (
    BasePersistenceLayer,
    DataRecord,
)
from aws_lambda_powertools.utilities.idempotency.serialization.pydantic import (
    PydanticSerializer,
)
from tests.functional.idempotency.utils import (
    hash_idempotency_key,
)
from tests.functional.utils import json_serialize

TESTS_MODULE_PREFIX = "test-func.tests.functional.idempotency._pydantic.test_idempotency_with_pydantic"


def get_dataclasses_lib():
    """Python 3.6 doesn't support dataclasses natively"""
    import dataclasses

    return dataclasses


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


@pytest.mark.parametrize("output_serializer_type", ["explicit", "deduced"])
def test_idempotent_function_serialization_pydantic(output_serializer_type: str):
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_serialization_pydantic.<locals>.collect_payment#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    class PaymentInput(BaseModel):
        customer_id: str
        transaction_id: str

    class PaymentOutput(BaseModel):
        customer_id: str
        transaction_id: str

    if output_serializer_type == "explicit":
        output_serializer = PydanticSerializer(
            model=PaymentOutput,
        )
    else:
        output_serializer = PydanticSerializer

    @idempotent_function(
        data_keyword_argument="payment",
        persistence_store=persistence_layer,
        config=config,
        output_serializer=output_serializer,
    )
    def collect_payment(payment: PaymentInput) -> PaymentOutput:
        return PaymentOutput(**payment.dict())

    # WHEN
    payment = PaymentInput(**mock_event)
    first_call: PaymentOutput = collect_payment(payment=payment)
    assert first_call.customer_id == payment.customer_id
    assert first_call.transaction_id == payment.transaction_id
    assert isinstance(first_call, PaymentOutput)
    second_call: PaymentOutput = collect_payment(payment=payment)
    assert isinstance(second_call, PaymentOutput)
    assert second_call.customer_id == payment.customer_id
    assert second_call.transaction_id == payment.transaction_id


def test_idempotent_function_serialization_pydantic_failure_no_return_type():
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_serialization_pydantic_failure_no_return_type.<locals>.collect_payment#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    class PaymentInput(BaseModel):
        customer_id: str
        transaction_id: str

    class PaymentOutput(BaseModel):
        customer_id: str
        transaction_id: str

    idempotent_function_decorator = idempotent_function(
        data_keyword_argument="payment",
        persistence_store=persistence_layer,
        config=config,
        output_serializer=PydanticSerializer,
    )
    with pytest.raises(IdempotencyNoSerializationModelError, match="No serialization model was supplied"):

        @idempotent_function_decorator
        def collect_payment(payment: PaymentInput):
            return PaymentOutput(**payment.dict())


def test_idempotent_function_serialization_pydantic_failure_bad_type():
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_serialization_pydantic_failure_no_return_type.<locals>.collect_payment#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    class PaymentInput(BaseModel):
        customer_id: str
        transaction_id: str

    class PaymentOutput(BaseModel):
        customer_id: str
        transaction_id: str

    idempotent_function_decorator = idempotent_function(
        data_keyword_argument="payment",
        persistence_store=persistence_layer,
        config=config,
        output_serializer=PydanticSerializer,
    )
    with pytest.raises(IdempotencyModelTypeError, match="Model type is not inherited from pydantic BaseModel"):

        @idempotent_function_decorator
        def collect_payment(payment: PaymentInput) -> dict:
            return PaymentOutput(**payment.dict())


def test_idempotent_function_serialization_dataclass_failure_bad_type():
    # GIVEN
    dataclasses = get_dataclasses_lib()
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_serialization_pydantic_failure_no_return_type.<locals>.collect_payment#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    @dataclasses.dataclass
    class PaymentInput:
        customer_id: str
        transaction_id: str

    @dataclasses.dataclass
    class PaymentOutput:
        customer_id: str
        transaction_id: str

    idempotent_function_decorator = idempotent_function(
        data_keyword_argument="payment",
        persistence_store=persistence_layer,
        config=config,
        output_serializer=PydanticSerializer,
    )
    with pytest.raises(IdempotencyModelTypeError, match="Model type is not inherited from pydantic BaseModel"):

        @idempotent_function_decorator
        def collect_payment(payment: PaymentInput) -> dict:
            return PaymentOutput(**payment.dict())


def test_idempotent_function_pydantic():
    # Scenario _prepare_data should convert a pydantic to a dict
    class Foo(BaseModel):
        name: str

    expected_result = {"name": "Bar"}
    data = Foo(name="Bar")
    as_dict = _prepare_data(data)
    assert as_dict == data.dict()
    assert as_dict == expected_result


@pytest.mark.parametrize("data", [None, "foo", ["foo"], 1, True, {}])
def test_idempotent_function_other(data):
    # All other data types should be left as is
    assert _prepare_data(data) == data


def test_idempotent_function_pydantic_with_jmespath():
    # GIVEN
    config = IdempotencyConfig(event_key_jmespath="transaction_id", use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_pydantic_with_jmespath.<locals>.collect_payment#{hash_idempotency_key(mock_event['transaction_id'])}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    class Payment(BaseModel):
        customer_id: str
        transaction_id: str

    @idempotent_function(data_keyword_argument="payment", persistence_store=persistence_layer, config=config)
    def collect_payment(payment: Payment):
        return payment.transaction_id

    # WHEN
    payment = Payment(**mock_event)
    result = collect_payment(payment=payment)

    # THEN idempotency key assertion happens at MockPersistenceLayer
    assert result == payment.transaction_id


@pytest.mark.parametrize("output_serializer_type", ["explicit", "deduced"])
def test_idempotent_function_serialization_pydantic_with_optional_return(output_serializer_type: str):
    # GIVEN
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"customer_id": "fake", "transaction_id": "fake-id"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_serialization_pydantic_with_optional_return.<locals>.collect_payment#{hash_idempotency_key(mock_event)}"  # noqa E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)

    class PaymentInput(BaseModel):
        customer_id: str
        transaction_id: str

    class PaymentOutput(BaseModel):
        customer_id: str
        transaction_id: str

    if output_serializer_type == "explicit":
        output_serializer = PydanticSerializer(
            model=PaymentOutput,
        )
    else:
        output_serializer = PydanticSerializer

    @idempotent_function(
        data_keyword_argument="payment",
        persistence_store=persistence_layer,
        config=config,
        output_serializer=output_serializer,
    )
    def collect_payment(payment: PaymentInput) -> PaymentOutput | None:
        return PaymentOutput(**payment.dict())

    # WHEN
    payment = PaymentInput(**mock_event)
    first_call: PaymentOutput = collect_payment(payment=payment)
    assert first_call.customer_id == payment.customer_id
    assert first_call.transaction_id == payment.transaction_id
    assert isinstance(first_call, PaymentOutput)
    second_call: PaymentOutput = collect_payment(payment=payment)
    assert isinstance(second_call, PaymentOutput)
    assert second_call.customer_id == payment.customer_id
    assert second_call.transaction_id == payment.transaction_id


class PaymentStatus(Enum):
    PAID = "paid"


class PaymentReceipt(BaseModel):
    payment_id: UUID
    paid_at: datetime
    status: PaymentStatus
    customer_id: str


@pytest.fixture
def payment_receipt() -> PaymentReceipt:
    return PaymentReceipt(
        payment_id=UUID("12345678-1234-5678-1234-567812345678"),
        paid_at=datetime(2024, 3, 20, 14, 30, tzinfo=timezone.utc),
        status=PaymentStatus.PAID,
        customer_id="c-456",
    )


def test_pydantic_serializer_round_trips_non_json_types(payment_receipt: PaymentReceipt):
    # GIVEN a serializer for a model with UUID, datetime and plain Enum fields
    serializer = PydanticSerializer(model=PaymentReceipt)

    # WHEN the model is stored as JSON, the same way the persistence layer saves a result
    stored = json_serialize(serializer.to_dict(payment_receipt))

    # THEN reading it back returns the same model
    assert serializer.from_dict(json.loads(stored)) == payment_receipt


@pytest.mark.parametrize("output_serializer_type", ["explicit", "deduced"])
def test_idempotent_function_serialization_pydantic_with_non_json_types(
    output_serializer_type: str,
    payment_receipt: PaymentReceipt,
    mocker: MockerFixture,
):
    # GIVEN a function that returns a model with UUID, datetime and plain Enum fields
    config = IdempotencyConfig(use_local_cache=True)
    mock_event = {"customer_id": "c-456", "transaction_id": "fake-id"}
    idempotency_key = f"{TESTS_MODULE_PREFIX}.test_idempotent_function_serialization_pydantic_with_non_json_types.<locals>.collect_payment#{hash_idempotency_key(mock_event)}"  # noqa: E501
    persistence_layer = MockPersistenceLayer(expected_idempotency_key=idempotency_key)
    update_record_spy = mocker.spy(persistence_layer, "_update_record")

    class PaymentInput(BaseModel):
        customer_id: str
        transaction_id: str

    if output_serializer_type == "explicit":
        output_serializer = PydanticSerializer(
            model=PaymentReceipt,
        )
    else:
        output_serializer = PydanticSerializer

    executions = []

    @idempotent_function(
        data_keyword_argument="payment",
        persistence_store=persistence_layer,
        config=config,
        output_serializer=output_serializer,
    )
    def collect_payment(payment: PaymentInput) -> PaymentReceipt:
        executions.append(payment)
        return payment_receipt

    # WHEN calling the function for the first time
    payment = PaymentInput(**mock_event)
    first_call = collect_payment(payment=payment)

    # THEN the result is saved as a COMPLETED record
    assert update_record_spy.call_args.kwargs["data_record"].status == "COMPLETED"

    # WHEN calling the function again with the same payment
    second_call = collect_payment(payment=payment)

    # THEN the saved result is returned as the model, without running the function again
    assert isinstance(second_call, PaymentReceipt)
    assert second_call == first_call
    assert executions == [payment]
