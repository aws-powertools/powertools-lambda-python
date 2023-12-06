import decimal
import json
from dataclasses import dataclass

import pytest
from pydantic import BaseModel

from aws_lambda_powertools.shared.json_encoder import Encoder


def test_jsonencode_decimal():
    result = json.dumps({"val": decimal.Decimal("8.5")}, cls=Encoder)
    assert result == '{"val": "8.5"}'


def test_jsonencode_decimal_nan():
    result = json.dumps({"val": decimal.Decimal("NaN")}, cls=Encoder)
    assert result == '{"val": NaN}'


def test_jsonencode_calls_default():
    class CustomClass:
        pass

    with pytest.raises(TypeError):
        json.dumps({"val": CustomClass()}, cls=Encoder)


def test_json_encode_pydantic():
    # GIVEN a Pydantic model
    class Model(BaseModel):
        data: dict

    data = {"msg": "hello"}
    model = Model(data=data)

    # WHEN json.dumps use our custom Encoder
    result = json.dumps(model, cls=Encoder)

    # THEN we should serialize successfully; not raise a TypeError
    assert result == json.dumps({"data": data}, cls=Encoder)


def test_json_encode_dataclasses():
    # GIVEN a standard dataclass

    @dataclass
    class Model:
        data: dict

    data = {"msg": "hello"}
    model = Model(data=data)

    # WHEN json.dumps use our custom Encoder
    result = json.dumps(model, cls=Encoder)

    # THEN we should serialize successfully; not raise a TypeError
    assert result == json.dumps({"data": data}, cls=Encoder)
