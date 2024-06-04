import math
from dataclasses import dataclass
from typing import List

import pytest
from pydantic import BaseModel
from pydantic.color import Color

from aws_lambda_powertools.event_handler.openapi.encoders import jsonable_encoder
from aws_lambda_powertools.event_handler.openapi.exceptions import SerializationError


def test_openapi_encode_include():
    class User(BaseModel):
        name: str
        age: int

    result = jsonable_encoder(User(name="John", age=20), include=["name"])
    assert result == {"name": "John"}


def test_openapi_encode_exclude():
    class User(BaseModel):
        name: str
        age: int

    result = jsonable_encoder(User(name="John", age=20), exclude=["age"])
    assert result == {"name": "John"}


def test_openapi_encode_pydantic():
    class Order(BaseModel):
        quantity: int

    class User(BaseModel):
        name: str
        order: Order

    result = jsonable_encoder(User(name="John", order=Order(quantity=2)))
    assert result == {"name": "John", "order": {"quantity": 2}}


@pytest.mark.usefixtures("pydanticv1_only")
def test_openapi_encode_pydantic_root_types():
    class User(BaseModel):
        __root__: List[str]

    result = jsonable_encoder(User(__root__=["John", "Jane"]))
    assert result == ["John", "Jane"]


def test_openapi_encode_dataclass():
    @dataclass
    class Order:
        quantity: int

    @dataclass
    class User:
        name: str
        order: Order

    result = jsonable_encoder(User(name="John", order=Order(quantity=2)))
    assert result == {"name": "John", "order": {"quantity": 2}}


def test_openapi_encode_enum():
    from enum import Enum

    class Color(Enum):
        RED = "red"
        GREEN = "green"
        BLUE = "blue"

    result = jsonable_encoder(Color.RED)
    assert result == "red"


def test_openapi_encode_purepath():
    from pathlib import PurePath

    result = jsonable_encoder(PurePath("/foo/bar"))
    assert result == "/foo/bar"


def test_openapi_encode_scalars():
    result = jsonable_encoder("foo")
    assert result == "foo"

    result = jsonable_encoder(1)
    assert result == 1

    result = jsonable_encoder(1.0)
    assert math.isclose(result, 1.0)

    result = jsonable_encoder(True)
    assert result is True

    result = jsonable_encoder(None)
    assert result is None


def test_openapi_encode_dict():
    result = jsonable_encoder({"foo": "bar"})
    assert result == {"foo": "bar"}


def test_openapi_encode_dict_with_include():
    result = jsonable_encoder({"foo": "bar", "bar": "foo"}, include=["foo"])
    assert result == {"foo": "bar"}


def test_openapi_encode_dict_with_exclude():
    result = jsonable_encoder({"foo": "bar", "bar": "foo"}, exclude=["bar"])
    assert result == {"foo": "bar"}


def test_openapi_encode_sequences():
    result = jsonable_encoder(["foo", "bar"])
    assert result == ["foo", "bar"]

    result = jsonable_encoder(("foo", "bar"))
    assert result == ["foo", "bar"]

    result = jsonable_encoder({"foo", "bar"})
    assert set(result) == {"foo", "bar"}

    result = jsonable_encoder(frozenset(("foo", "bar")))
    assert set(result) == {"foo", "bar"}


def test_openapi_encode_bytes():
    result = jsonable_encoder(b"foo")
    assert result == "foo"


def test_openapi_encode_timedelta():
    from datetime import timedelta

    result = jsonable_encoder(timedelta(seconds=1))
    assert result == 1


def test_openapi_encode_decimal():
    from decimal import Decimal

    result = jsonable_encoder(Decimal("1.0"))
    assert math.isclose(result, 1.0)

    result = jsonable_encoder(Decimal("1"))
    assert result == 1


def test_openapi_encode_uuid():
    from uuid import UUID

    result = jsonable_encoder(UUID("123e4567-e89b-12d3-a456-426614174000"))
    assert result == "123e4567-e89b-12d3-a456-426614174000"


def test_openapi_encode_encodable():
    from datetime import date, datetime, time

    result = jsonable_encoder(date(2021, 1, 1))
    assert result == "2021-01-01"

    result = jsonable_encoder(datetime(2021, 1, 1, 0, 0, 0))
    assert result == "2021-01-01T00:00:00"

    result = jsonable_encoder(time(0, 0, 0))
    assert result == "00:00:00"


def test_openapi_encode_subclasses():
    class MyColor(Color):
        pass

    result = jsonable_encoder(MyColor("red"))
    assert result == "red"


def test_openapi_encode_other():
    class User:
        def __init__(self, name: str):
            self.name = name

    result = jsonable_encoder(User(name="John"))
    assert result == {"name": "John"}


def test_openapi_encode_with_error():
    class MyClass:
        __slots__ = []

    with pytest.raises(SerializationError, match="Unable to serializer the object*"):
        jsonable_encoder(MyClass())
