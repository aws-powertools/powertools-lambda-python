import decimal
import json

import pytest

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
