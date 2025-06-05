from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.kafka_consumer.deserializer.base import DeserializerBase


def get_deserializer(schema_type: str, schema_value: Any) -> DeserializerBase:
    if schema_type == "AVRO":
        # Import here to avoid dependency if not used
        from aws_lambda_powertools.utilities.kafka_consumer.deserializer.avro import AvroDeserializer

        return AvroDeserializer(schema_value)
    elif schema_type == "PROTOBUF":
        # Import here to avoid dependency if not used
        from aws_lambda_powertools.utilities.kafka_consumer.deserializer.protobuf import ProtobufDeserializer

        return ProtobufDeserializer(schema_value)
    elif schema_type == "JSON":
        # Import here to avoid dependency if not used
        from aws_lambda_powertools.utilities.kafka_consumer.deserializer.json import JsonDeserializer

        return JsonDeserializer()
    else:
        raise ValueError(f"Invalid schema_type: {schema_type}")
