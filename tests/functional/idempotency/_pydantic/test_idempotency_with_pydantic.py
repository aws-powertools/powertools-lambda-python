import pytest
from pydantic import BaseModel

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

TESTS_MODULE_PREFIX = "test-func.tests.functional.idempotency._pydantic.test_idempotency_with_pydantic"


def get_dataclasses_lib():
    """Python 3.6 doesn't support dataclasses natively"""
    import dataclasses

    return dataclasses


class MockPersistenceLayer(BasePersistenceLayer):
    def __init__(self, expected_idempotency_key: str):
        self.expected_idempotency_key = expected_idempotency_key
        super(MockPersistenceLayer, self).__init__()

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
