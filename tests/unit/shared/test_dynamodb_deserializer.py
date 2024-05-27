from typing import Any, Dict, Optional

import pytest

from aws_lambda_powertools.shared.dynamodb_deserializer import TypeDeserializer


class DeserialiserModel:
    def __init__(self, data: dict):
        self._data = data
        self._deserializer = TypeDeserializer()

    def _deserialize_dynamodb_dict(self) -> Optional[Dict[str, Any]]:
        if self._data is None:
            return None

        return {k: self._deserializer.deserialize(v) for k, v in self._data.items()}

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        """The primary key attribute(s) for the DynamoDB item that was modified."""
        return self._deserialize_dynamodb_dict()


def test_deserializer():
    model = DeserialiserModel(
        {
            "Id": {"S": "Id-123"},
            "Name": {"S": "John Doe"},
            "ZipCode": {"N": 12345},
            "Things": {"L": [{"N": 0}, {"N": 1}, {"N": 2}, {"N": 3}]},
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
