# Postponed annotations turn every annotation in this module into a string, as in customer code that uses
# `from __future__ import annotations`. Models are defined at module level, where customers define them.
from __future__ import annotations

import dataclasses

import pytest
from pydantic import BaseModel

from aws_lambda_powertools.utilities.idempotency import (
    IdempotencyConfig,
    idempotent_function,
)
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyModelTypeError,
)
from aws_lambda_powertools.utilities.idempotency.persistence.base import (
    BasePersistenceLayer,
    DataRecord,
)
from aws_lambda_powertools.utilities.idempotency.serialization.dataclass import (
    DataclassSerializer,
)
from aws_lambda_powertools.utilities.idempotency.serialization.pydantic import (
    PydanticSerializer,
)


class PaymentInput(BaseModel):
    customer_id: str
    transaction_id: str


class PaymentOutput(BaseModel):
    customer_id: str
    transaction_id: str


@dataclasses.dataclass
class PaymentOutputDataclass:
    customer_id: str
    transaction_id: str


class NoOpPersistenceLayer(BasePersistenceLayer):
    # Responses are replayed from the local cache, so the store itself doesn't need to keep anything
    def _put_record(self, data_record: DataRecord) -> None: ...

    def _update_record(self, data_record: DataRecord) -> None: ...

    def _get_record(self, idempotency_key) -> DataRecord: ...

    def _delete_record(self, data_record: DataRecord) -> None: ...


MOCK_EVENT = {"customer_id": "fake", "transaction_id": "fake-id"}


def test_idempotent_function_pydantic_serializer_deduced_from_postponed_annotation():
    # GIVEN a function annotated with a Pydantic model under postponed annotations
    @idempotent_function(
        data_keyword_argument="payment",
        persistence_store=NoOpPersistenceLayer(),
        config=IdempotencyConfig(use_local_cache=True),
        output_serializer=PydanticSerializer,
    )
    def collect_payment(payment: PaymentInput) -> PaymentOutput:
        return PaymentOutput(**payment.model_dump())

    # WHEN calling it twice with the same payload
    payment = PaymentInput(**MOCK_EVENT)
    first_call = collect_payment(payment=payment)
    second_call = collect_payment(payment=payment)

    # THEN the replayed response is rebuilt as the annotated model
    assert isinstance(first_call, PaymentOutput)
    assert isinstance(second_call, PaymentOutput)
    assert second_call == first_call


def test_idempotent_function_pydantic_serializer_deduced_from_postponed_optional_annotation():
    # GIVEN a function annotated with an optional Pydantic model under postponed annotations
    @idempotent_function(
        data_keyword_argument="payment",
        persistence_store=NoOpPersistenceLayer(),
        config=IdempotencyConfig(use_local_cache=True),
        output_serializer=PydanticSerializer,
    )
    def collect_payment(payment: PaymentInput) -> PaymentOutput | None:
        return PaymentOutput(**payment.model_dump())

    # WHEN calling it twice with the same payload
    payment = PaymentInput(**MOCK_EVENT)
    collect_payment(payment=payment)
    second_call = collect_payment(payment=payment)

    # THEN the replayed response is rebuilt as the annotated model
    assert isinstance(second_call, PaymentOutput)


def test_idempotent_function_dataclass_serializer_deduced_from_postponed_annotation():
    # GIVEN a function annotated with a dataclass under postponed annotations
    @idempotent_function(
        data_keyword_argument="payment",
        persistence_store=NoOpPersistenceLayer(),
        config=IdempotencyConfig(use_local_cache=True),
        output_serializer=DataclassSerializer,
    )
    def collect_payment(payment: dict) -> PaymentOutputDataclass:
        return PaymentOutputDataclass(**payment)

    # WHEN calling it twice with the same payload
    collect_payment(payment=MOCK_EVENT)
    second_call = collect_payment(payment=MOCK_EVENT)

    # THEN the replayed response is rebuilt as the annotated dataclass
    assert isinstance(second_call, PaymentOutputDataclass)
    assert second_call == PaymentOutputDataclass(**MOCK_EVENT)


def test_idempotent_function_pydantic_serializer_postponed_list_annotation_raises_model_type_error():
    idempotent_function_decorator = idempotent_function(
        data_keyword_argument="payment",
        persistence_store=NoOpPersistenceLayer(),
        output_serializer=PydanticSerializer,
    )

    # GIVEN a function annotated with a list of models, which isn't a Pydantic model
    # WHEN decorating it
    # THEN we raise IdempotencyModelTypeError instead of a TypeError from issubclass
    with pytest.raises(IdempotencyModelTypeError, match="Model type is not inherited from pydantic BaseModel"):

        @idempotent_function_decorator
        def collect_payment(payment: PaymentInput) -> list[PaymentOutput]:
            return [PaymentOutput(**payment.model_dump())]


def test_idempotent_function_pydantic_serializer_unresolvable_postponed_annotation_raises_model_type_error():
    # GIVEN a model defined inside a function, which postponed annotations can't resolve from module globals
    class LocalPaymentOutput(BaseModel):
        customer_id: str

    idempotent_function_decorator = idempotent_function(
        data_keyword_argument="payment",
        persistence_store=NoOpPersistenceLayer(),
        output_serializer=PydanticSerializer,
    )

    # WHEN decorating a function annotated with it
    # THEN we raise IdempotencyModelTypeError instead of a TypeError from issubclass
    with pytest.raises(IdempotencyModelTypeError, match="Model type is not inherited from pydantic BaseModel"):

        @idempotent_function_decorator
        def collect_payment(payment: PaymentInput) -> LocalPaymentOutput:
            return LocalPaymentOutput(customer_id=payment.customer_id)
