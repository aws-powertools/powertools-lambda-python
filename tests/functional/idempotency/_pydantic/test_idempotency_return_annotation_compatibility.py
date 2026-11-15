import functools
import sys
from typing import TYPE_CHECKING, Annotated, get_args, get_origin, no_type_check

import pytest

from aws_lambda_powertools.utilities.idempotency import IdempotencyConfig, idempotent_function
from aws_lambda_powertools.utilities.idempotency.serialization.base import BaseIdempotencyModelSerializer
from aws_lambda_powertools.utilities.idempotency.serialization.dataclass import DataclassSerializer
from aws_lambda_powertools.utilities.idempotency.serialization.pydantic import PydanticSerializer
from tests.functional.idempotency._pydantic.test_idempotency_with_postponed_annotations import (
    MOCK_EVENT,
    NoOpPersistenceLayer,
    PaymentOutput,
    PaymentOutputDataclass,
)

if TYPE_CHECKING:
    from collections.abc import Mapping as InputOnlyAvailableToTypeChecker


class MetadataSerializer(BaseIdempotencyModelSerializer):
    @classmethod
    def instantiate(cls, model_type):
        assert get_origin(model_type) is Annotated
        model, metadata = get_args(model_type)
        assert metadata == "v1"
        return PydanticSerializer(model=model)

    def to_dict(self, data): ...

    def from_dict(self, data): ...


def replay(function, serializer, expected):
    config = IdempotencyConfig(use_local_cache=True)

    # This fake Lambda context avoids depending on DynamoDB or warning about missing context.
    class Context:
        def get_remaining_time_in_millis(self):
            return 1000

    config.register_lambda_context(Context())
    decorated = idempotent_function(
        function,
        data_keyword_argument="payment",
        persistence_store=NoOpPersistenceLayer(),
        config=config,
        output_serializer=serializer,
    )
    assert decorated(payment=MOCK_EVENT) == expected
    assert decorated(payment=MOCK_EVENT) == expected


@pytest.mark.parametrize("postponed", [False, True])
def test_custom_serializer_keeps_annotated_metadata(postponed):
    calls = []

    def collect_payment(payment: dict) -> Annotated[PaymentOutput, "v1"]:
        calls.append(payment)
        return PaymentOutput(**payment)

    if postponed:
        collect_payment.__annotations__["return"] = "Annotated[PaymentOutput, 'v1']"

    replay(collect_payment, MetadataSerializer, PaymentOutput(**MOCK_EVENT))
    assert len(calls) == 1


@pytest.mark.parametrize("postponed", [False, True])
def test_no_type_check_keeps_return_model(postponed):
    calls = []

    @no_type_check
    def collect_payment(payment: dict) -> PaymentOutput:
        calls.append(payment)
        return PaymentOutput(**payment)

    if postponed:
        collect_payment.__annotations__["return"] = "PaymentOutput"

    replay(collect_payment, PydanticSerializer, PaymentOutput(**MOCK_EVENT))
    assert len(calls) == 1


@pytest.mark.parametrize(
    "model,serializer",
    [(PaymentOutput, PydanticSerializer), (PaymentOutputDataclass, DataclassSerializer)],
)
def test_unresolved_input_annotation_does_not_block_return_model(model, serializer):
    calls = []

    def collect_payment(payment: "InputOnlyAvailableToTypeChecker"):
        calls.append(payment)
        return model(**payment)

    collect_payment.__annotations__["return"] = model.__name__
    replay(collect_payment, serializer, model(**MOCK_EVENT))
    assert len(calls) == 1


def test_wrapped_function_resolves_return_in_original_namespace():
    calls = []

    def collect_payment(payment: dict) -> "PaymentOutput":
        calls.append(payment)
        return PaymentOutput(**payment)

    # A wrapper from a different module has no PaymentOutput in its globals.
    namespace = {"functools": functools, "original": collect_payment}
    exec(
        compile(
            "@functools.wraps(original)\ndef wrapper(*args, **kwargs):\n    return original(*args, **kwargs)\n",
            "<external_wrapper>",
            "exec",
            dont_inherit=True,
        ),
        namespace,
    )
    replay(namespace["wrapper"], PydanticSerializer, PaymentOutput(**MOCK_EVENT))
    assert len(calls) == 1


@pytest.mark.skipif(sys.version_info < (3, 14), reason="Native deferred annotations require Python 3.14")
def test_native_deferred_annotations_allow_unresolved_input():
    calls = []
    namespace = {"PaymentOutput": PaymentOutput, "calls": calls}
    exec(
        compile(
            "def collect_payment(payment: InputOnlyAvailableToTypeChecker) -> PaymentOutput:\n"
            "    calls.append(payment)\n"
            "    return PaymentOutput(**payment)\n",
            "<native_deferred_annotations>",
            "exec",
            dont_inherit=True,
        ),
        namespace,
    )
    replay(namespace["collect_payment"], PydanticSerializer, PaymentOutput(**MOCK_EVENT))
    assert len(calls) == 1
