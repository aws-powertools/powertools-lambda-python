from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import TypeAdapter

from aws_lambda_powertools.utilities.kafka.serialization.base import OutputSerializerBase

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.kafka.serialization.types import T


class PydanticOutputSerializer(OutputSerializerBase):
    def serialize(self, data: dict[str, Any], output_class: type[T] | None = None) -> T | dict[str, Any]:
        if output_class is None:
            return data

        # Use TypeAdapter for better support of Union types and other complex types
        adapter = TypeAdapter(output_class)
        return adapter.validate_python(data)
