from __future__ import annotations

import dataclasses

import pytest
from pydantic import BaseModel

from aws_lambda_powertools.utilities.data_masking.base import DataMasking, prepare_data
from aws_lambda_powertools.utilities.data_masking.constants import DATA_MASKING_STRING


@pytest.fixture
def data_masker() -> DataMasking:
    return DataMasking()


def test_prepare_data_primitive():
    assert prepare_data("hello") == "hello"
    assert prepare_data(123) == 123
    assert prepare_data(3.14) == pytest.approx(3.14)
    assert prepare_data(True) is True
    assert prepare_data(None) is None


def test_prepare_data_dict_no_change():
    data = {"x": "y", "z": 10}
    result = prepare_data(data)
    assert isinstance(result, dict)
    assert result == data


def test_prepare_data_list():
    data = [1, "a", {"b": 2}]
    result = prepare_data(data)
    assert isinstance(result, list)
    assert result == [1, "a", {"b": 2}]


def test_prepare_data_tuple():
    data = (1, 2, {"a": 3})
    result = prepare_data(data)
    assert isinstance(result, tuple)
    assert result[2]["a"] == 3


def test_prepare_data_set():
    data = {1, 2, 3}
    result = prepare_data(data)
    assert isinstance(result, set)
    assert result == {1, 2, 3}


def test_prepare_data_dataclass():
    @dataclasses.dataclass
    class MyDataClass:
        name: str
        age: int

    instance = MyDataClass(name="delta", age=50)
    result = prepare_data(instance)
    assert isinstance(result, dict)
    assert result["name"] == "delta"
    assert result["age"] == 50


def test_prepare_data_pydantic():
    class MyPydanticModel(BaseModel):
        name: str
        age: int

    instance = MyPydanticModel(name="alpha", age=30)
    result = prepare_data(instance)
    assert isinstance(result, dict)
    assert result["name"] == "alpha"
    assert result["age"] == 30


def test_prepare_data_custom_class_with_dict():
    class MyCustom:
        def __init__(self, name, age):
            self.name = name
            self.age = age

        def dict(self):
            return {"name": self.name, "age": self.age}

    instance = MyCustom("beta", 40)
    result = prepare_data(instance)
    assert isinstance(result, dict)
    assert result["name"] == "beta"
    assert result["age"] == 40


def test_prepare_data_fallback_dict_via_dunder():
    class WithDict:
        def __init__(self, value):
            self.value = value

    instance = WithDict(100)
    result = prepare_data(instance)
    assert isinstance(result, dict)
    assert result["value"] == 100


def test_prepare_data_nested_structure():
    @dataclasses.dataclass
    class NestedDC:
        x: int
        y: str

    class NestedPM(BaseModel):
        a: int
        b: str

    class NestedCustom:
        def __init__(self, z):
            self.z = z

        def dict(self):
            return {"z": self.z}

    data = {
        "dc": NestedDC(x=10, y="foo"),
        "pm": NestedPM(a=5, b="bar"),
        "custom": NestedCustom(z="baz"),
        "nested": {"list": [NestedDC(x=1, y="inner"), NestedPM(a=2, b="inner2")]},
    }
    result = prepare_data(data)
    assert result["dc"]["x"] == 10
    assert result["dc"]["y"] == "foo"
    assert result["pm"]["a"] == 5
    assert result["pm"]["b"] == "bar"
    assert result["custom"]["z"] == "baz"
    assert result["nested"]["list"][0]["y"] == "inner"
    assert result["nested"]["list"][1]["a"] == 2


def test_prepare_data_circular_reference():
    data = {"a": 1}
    data["self"] = data
    result = prepare_data(data)
    assert result["a"] == 1
    assert "self" in result


class MyPydanticModel(BaseModel):
    name: str
    age: int


@dataclasses.dataclass
class MyDataClass:
    name: str
    age: int


class MyCustomClass:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def dict(self):
        return {"name": self.name, "age": self.age}


def test_erase_on_pydantic_model(data_masker):
    instance = MyPydanticModel(name="powertools", age=5)
    result = data_masker.erase(instance, fields=["age"])
    assert isinstance(result, dict)
    assert result["age"] == DATA_MASKING_STRING
    assert result["name"] == "powertools"


def test_erase_on_dataclass(data_masker):
    instance = MyDataClass(name="powertools", age=5)
    result = data_masker.erase(instance, fields=["age"])
    assert isinstance(result, dict)
    assert result["age"] == DATA_MASKING_STRING
    assert result["name"] == "powertools"


def test_erase_on_custom_class(data_masker):
    instance = MyCustomClass("powertools", 5)
    result = data_masker.erase(instance, fields=["age"])
    assert isinstance(result, dict)
    assert result["age"] == DATA_MASKING_STRING
    assert result["name"] == "powertools"


def test_erase_on_nested_complex_structure(data_masker):
    @dataclasses.dataclass
    class NestedDC:
        value: int

    class NestedPM(BaseModel):
        value: int

    class MyCustomClass:
        def __init__(self, name, age):
            self.name = name
            self.age = age

        def dict(self):
            return {"name": self.name, "age": self.age}

    data = {
        "pydantic": NestedPM(value=10),
        "dataclass": NestedDC(value=20),
        "custom": MyCustomClass("example", 30),
        "plain_dict": {"value": 40},
        "list": [NestedPM(value=50), {"value": 60}],
    }
    result = data_masker.erase(data, fields=["$..value"])
    assert result["pydantic"]["value"] == DATA_MASKING_STRING
    assert result["dataclass"]["value"] == DATA_MASKING_STRING
    assert result["custom"] == {"name": "example", "age": 30}
    assert result["plain_dict"]["value"] == DATA_MASKING_STRING
    assert result["list"][0]["value"] == DATA_MASKING_STRING
    assert result["list"][1]["value"] == DATA_MASKING_STRING


def test_erase_pydantic_secret_fields_are_not_exposed():
    # GIVEN a model with SecretStr and SecretBytes fields
    from pydantic import SecretBytes, SecretStr

    class Login(BaseModel):
        user: str
        token: SecretStr
        key: SecretBytes

    model = Login(user="pat", token=SecretStr("tok-value"), key=SecretBytes(b"key-value"))

    # WHEN erasing another field
    result = DataMasking().erase(model, fields=["user"])

    # THEN the secret fields keep Pydantic's masked rendering instead of the raw value
    assert result["user"] == DATA_MASKING_STRING
    assert result["token"] == "**********"
    assert result["key"] == "**********"
    assert "tok-value" not in str(result) and "key-value" not in str(result)


def test_erase_pydantic_non_json_field_types():
    # GIVEN a model with UUID, datetime and Decimal fields
    import datetime as dt
    import uuid
    from decimal import Decimal

    class Order(BaseModel):
        id: uuid.UUID
        created: dt.datetime
        total: Decimal
        customer: str

    model = Order(
        id=uuid.UUID(int=1),
        created=dt.datetime(2026, 1, 2, 3, 4, 5),
        total=Decimal("9.50"),
        customer="Pat",
    )

    # WHEN erasing through the fields path, which serializes to JSON internally
    result = DataMasking().erase(model, fields=["customer"])

    # THEN it no longer fails with TypeError and the other fields are JSON-safe values
    assert result["customer"] == DATA_MASKING_STRING
    assert result["id"] == "00000000-0000-0000-0000-000000000001"
    assert result["created"] == "2026-01-02T03:04:05"
    assert result["total"] == "9.50"


def test_prepare_data_nested_models_referenced_twice():
    # GIVEN a model used twice inside the same payload
    class Address(BaseModel):
        city: str

    class Order(BaseModel):
        shipping: Address
        billing: Address

    address = Address(city="Lisbon")

    # WHEN preparing the data
    result = prepare_data(Order(shipping=address, billing=address))

    # THEN both references are converted
    assert result == {"shipping": {"city": "Lisbon"}, "billing": {"city": "Lisbon"}}
