from __future__ import annotations

import json

from aws_lambda_powertools.utilities.kafka_consumer.deserializer.base import DeserializerBase
from aws_lambda_powertools.utilities.kafka_consumer.exceptions import KafkaConsumerDeserializationError


class JsonDeserializer(DeserializerBase):
    def deserialize(self, data: bytes | str) -> dict:
        try:
            value = self._decode_input(data)
            return json.loads(value.decode("utf-8"))
        except Exception as e:
            raise KafkaConsumerDeserializationError(
                f"JSON deserialization error: {type(e).__name__}: {str(e)}",
            ) from e
