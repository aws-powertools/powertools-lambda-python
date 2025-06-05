from __future__ import annotations

from typing import Any

from google.protobuf.json_format import MessageToDict

from aws_lambda_powertools.utilities.kafka_consumer.deserializer.base import DeserializerBase
from aws_lambda_powertools.utilities.kafka_consumer.exceptions import (
    KafkaConsumerDeserializationError,
)


class ProtobufDeserializer(DeserializerBase):
    def __init__(self, message_class: Any):
        self.message_class = message_class

    def deserialize(self, data: bytes | str) -> dict:
        try:
            value = self._decode_input(data)
            message = self.message_class()
            message.ParseFromString(value)
            return MessageToDict(message, preserving_proto_field_name=True)
        except Exception as e:
            raise KafkaConsumerDeserializationError(
                f"Protocol Buffer deserialization error: {type(e).__name__}: {str(e)}",
            ) from e
