from __future__ import annotations

import io
from typing import Any

from avro.io import BinaryDecoder, DatumReader
from avro.schema import parse as parse_schema

from aws_lambda_powertools.utilities.kafka_consumer.deserializer.base import DeserializerBase
from aws_lambda_powertools.utilities.kafka_consumer.exceptions import (
    KafkaConsumerAvroMissingSchemaError,
    KafkaConsumerDeserializationError,
)


class AvroDeserializer(DeserializerBase):
    def __init__(self, schema_str: str):
        if not schema_str:
            raise KafkaConsumerAvroMissingSchemaError("Schema string must be provided for Avro deserialization")
        self.parsed_schema = parse_schema(schema_str)
        self.reader = DatumReader(self.parsed_schema)

    def deserialize(self, data: bytes | str) -> dict[str, Any]:
        try:
            value = self._decode_input(data)
            bytes_reader = io.BytesIO(value)
            decoder = BinaryDecoder(bytes_reader)
            return self.reader.read(decoder)
        except (TypeError, ValueError) as e:
            raise KafkaConsumerDeserializationError(
                f"Avro deserialization error: {type(e).__name__}: {str(e)}",
            ) from e
