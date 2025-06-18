from __future__ import annotations

from dataclasses import is_dataclass
from typing import Any, cast

from aws_lambda_powertools.utilities.kafka.serialization.base import OutputSerializerBase
from aws_lambda_powertools.utilities.kafka.serialization.types import T


class DataclassOutputSerializer(OutputSerializerBase):
    def serialize(self, data: dict[str, Any], output_class: type[T] | None = None) -> T | dict[str, Any]:
        if output_class is None:
            return data

        if not is_dataclass(output_class):
            raise ValueError("Output class must be a dataclass")

        return cast(T, output_class(**data))
