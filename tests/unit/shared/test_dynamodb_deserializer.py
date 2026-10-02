from __future__ import annotations

from decimal import ROUND_UP, Decimal, Inexact, Overflow, Rounded, localcontext
from typing import Any

import pytest

from aws_lambda_powertools.shared.dynamodb_deserializer import TypeDeserializer


class DeserialiserModel:
    def __init__(self, data: dict):
        self._data = data
        self._deserializer = TypeDeserializer()

    def _deserialize_dynamodb_dict(self) -> dict[str, Any] | None:
        if self._data is None:
            return None

        return {k: self._deserializer.deserialize(v) for k, v in self._data.items()}

    @property
    def data(self) -> dict[str, Any] | None:
        """The primary key attribute(s) for the DynamoDB item that was modified."""
        return self._deserialize_dynamodb_dict()


def test_deserializer():
    model = DeserialiserModel(
        {
            "Id": {"S": "Id-123"},
            "Name": {"S": "John Doe"},
            "ZipCode": {"N": "12345"},
            "Things": {"L": [{"N": "0"}, {"N": "1"}, {"N": "2"}, {"N": "3"}]},
            "MoreThings": {"M": {"a": {"S": "foo"}, "b": {"S": "bar"}}},
        },
    )

    assert model.data.get("Id") == "Id-123"
    assert model.data.get("Name") == "John Doe"
    assert model.data.get("ZipCode") == 12345
    assert model.data.get("Things") == [0, 1, 2, 3]
    assert model.data.get("MoreThings") == {"a": "foo", "b": "bar"}


def test_deserializer_error():
    model = DeserialiserModel(
        {
            "Id": {"X": None},
        },
    )

    with pytest.raises(TypeError):
        model.data.get("Id")


@pytest.mark.parametrize(
    "value",
    [
        "-12345678901234567890123456789012345678",
        "1.2345678901234567890123456789012345678",
        "110111111111111110000000000000000000000",
        "12345678901234567890123456789012345678000",
    ],
)
def test_deserializer_keeps_value_of_numbers_with_38_digits_of_precision(value):
    assert TypeDeserializer().deserialize({"N": value}) == Decimal(value)


@pytest.mark.parametrize(
    "value",
    [
        "9" * 39,
        "-" + "9" * 39,
        "1" * 37 + "25",
        "1" * 37 + "35",
        "1." + "2" * 38,
        "123456789012345678901234567890123456789000",
        "123456789012345678901234567890123456789E-100",
        "1" * 39 + "E-9999999",
    ],
)
def test_deserializer_rejects_inexact_numbers(value):
    with pytest.raises(Inexact):
        TypeDeserializer().deserialize({"N": value})


@pytest.mark.parametrize("value", ["0E+0", "0E-100", "0e-130", "000E+5", "+0E-10", "-0E-100"])
def test_deserializer_preserves_scientific_zero(value):
    assert TypeDeserializer().deserialize({"N": value}) == Decimal(0)


@pytest.mark.parametrize("value", ["", ".", "0", "000", "000.", "0.000", "-0", "+0"])
def test_deserializer_preserves_existing_zero_handling(value):
    assert TypeDeserializer().deserialize({"N": value}) == Decimal(0)


@pytest.mark.parametrize(
    "value",
    [
        "00012345678901234567890123456789012345678000",
        "-12345678901234567890123456789012345678000",
        "1.2345678901234567890123456789012345678000",
        "12345678901234567890123456789012345678000E-40",
        "1000000000000000000000000000000000000000E-167",
        "99999999999999999999999999999999999999000E+85",
    ],
)
def test_deserializer_removes_only_exact_trailing_zeros(value):
    # Application Decimal settings must not affect deserialization.
    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_UP
        context.traps[Inexact] = True
        context.traps[Rounded] = True
        assert TypeDeserializer().deserialize({"N": value}) == Decimal(value)


@pytest.mark.parametrize(
    "value",
    [
        {"NS": ["1", "9" * 39]},
        {"L": [{"N": "9" * 39}]},
        {"M": {"amount": {"N": "9" * 39}}},
    ],
)
def test_deserializer_rejects_inexact_numbers_in_collections(value):
    with pytest.raises(Inexact):
        TypeDeserializer().deserialize(value)


def test_deserializer_keeps_distinct_number_set_values():
    values = ["1.2345678901234567890123456789012345677", "1.2345678901234567890123456789012345678"]

    assert TypeDeserializer().deserialize({"NS": values}) == {Decimal(value) for value in values}


def test_deserializer_normalization_preserves_overflow_errors():
    with pytest.raises(Overflow):
        TypeDeserializer().deserialize({"N": "1" * 38 + "00E+9999999"})
