from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.kafka_consumer.serialization.base import OutputSerializerBase

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.kafka_consumer.serialization.types import T


class CustomDictOutputSerializer(OutputSerializerBase):
    def serialize(self, data: dict[str, Any], output_class: type[T] | None = None) -> T | dict[str, Any]:
        if output_class is None:
            return data

        if not hasattr(output_class, "to_dict") and not hasattr(output_class, "from_dict"):
            raise ValueError("Output class must have to_dict or from_dict method")

        if hasattr(output_class, "from_dict"):
            return output_class.from_dict(data)

        # Instantiate and then populate
        instance = output_class()
        for key, value in data.items():
            setattr(instance, key, value)
        return instance
