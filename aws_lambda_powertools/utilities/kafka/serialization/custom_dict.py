from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.kafka.exceptions import KafkaConsumerOutputSerializerError
from aws_lambda_powertools.utilities.kafka.serialization.base import OutputSerializerBase

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.kafka.serialization.types import T


class CustomDictOutputSerializer(OutputSerializerBase):
    def serialize(self, data: dict[str, Any], output_class: type[T] | None = None) -> T | dict[str, Any]:
        if output_class is None:
            return data

        if not hasattr(output_class, "to_dict"):
            raise KafkaConsumerOutputSerializerError("The output serialization class must have to_dict method")

        # Instantiate and then populate
        instance = output_class
        for key, value in data.items():
            setattr(instance, key, value)
        return instance
