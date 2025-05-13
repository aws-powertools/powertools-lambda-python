from __future__ import annotations

import base64
import io
from typing import Any

from avro.io import BinaryDecoder, DatumReader
from avro.schema import parse as parse_schema
from google.protobuf.json_format import MessageToDict

from aws_lambda_powertools.utilities.kafka_consumer.exceptions import (
    KafkaConsumerAvroMissingSchemaError,
    KafkaConsumerAvroSchemaMismatchError,
    KafkaConsumerDeserializationError,
)


def deserialize_avro(avro_bytes: bytes | str, value_schema_str: str) -> dict:
    """
    Deserialize Avro binary data to Python dictionary objects.

    This function handles the deserialization of Avro-formatted binary data
    using a specified schema string. It supports both raw bytes and
    base64-encoded string inputs.

    Parameters
    ----------
    avro_bytes : bytes or str
        Avro binary data, either as raw bytes or base64-encoded string.
        If a string is provided, it will be treated as base64-encoded.
    value_schema_str : str
        Avro schema definition in JSON string format to use for reading.
        Must be a valid Avro schema definition.

    Returns
    -------
    Any
        Deserialized Python dictionary representing the Avro data.

    Raises
    ------
    KafkaConsumerAvroMissingSchemaError
        If the schema is not provided
    KafkaConsumerAvroSchemaMismatchError
        If there's a schema mismatch
    KafkaConsumerDeserializationError
        If deserialization fails due to data corruption.
    TypeError
        If avro_bytes is neither bytes nor a base64-encoded string.

    Examples
    --------
    >>> schema_str = '{"type": "record", "name": "User", "fields": [{"name": "name", "type": "string"}]}'
    >>> encoded_data = base64.b64encode(b'some-avro-binary-data')
    >>> user_dict = deserialize_avro(encoded_data, schema_str)
    """
    if not value_schema_str:
        raise KafkaConsumerAvroMissingSchemaError("Schema string must be provided for Avro deserialization")

    try:
        # Parse the provided schema
        parsed_schema = parse_schema(value_schema_str)
        reader = DatumReader(parsed_schema)

        # Handle different input types
        if isinstance(avro_bytes, str):
            # Assume base64 encoded string
            value = base64.b64decode(avro_bytes)
        elif isinstance(avro_bytes, bytes):
            # Already raw bytes
            value = avro_bytes
        else:
            # Try base64 decoding as a fallback
            try:
                value = base64.b64decode(avro_bytes)
            except Exception as e:
                raise TypeError(
                    f"Expected bytes or base64-encoded string, got {type(avro_bytes).__name__}. Error: {str(e)}",
                ) from e

        # Create binary decoder and read data
        bytes_reader = io.BytesIO(value)
        decoder = BinaryDecoder(bytes_reader)
        return reader.read(decoder)

    except KafkaConsumerAvroSchemaMismatchError as e:
        raise ValueError(
            f"Schema mismatch detected: Message schema doesn't match expected schema. "
            f"Details: {str(e)}. Verify schema registry configuration and message format.",
        ) from e
    except KafkaConsumerDeserializationError as e:
        raise ValueError(
            f"Deserialization failed: Unable to decode message data using Avro schema. "
            f"Error: {str(e)}. Check for data corruption or schema evolution issues.",
        ) from e


def deserialize_protobuf_with_compiled_classes(
    protobuf_bytes: bytes | str,
    message_class: Any,
) -> dict[str, Any]:
    """
    A deserialize that works with pre-compiled protobuf classes.

    Parameters
    ----------
    protobuf_bytes : Union[bytes, str]
        Protocol Buffer binary data, either as raw bytes or base64-encoded string.
    message_class : Any
        The pre-compiled Protocol Buffer message class.

    Returns
    -------
    Dict[str, Any]
        Deserialized Python dictionary representing the Protocol Buffer data.

    Example
    -------
    >>> from my_proto_package.user_pb2 import User
    >>> user_dict = deserialize_protobuf_with_compiled_classes(encoded_data, User)
    """

    try:
        # Handle different input types for the binary data
        if isinstance(protobuf_bytes, str):
            # Assume base64 encoded string
            value = base64.b64decode(protobuf_bytes)
        elif isinstance(protobuf_bytes, bytes):
            # Already raw bytes
            value = protobuf_bytes
        else:
            # Try base64 decoding as a fallback
            try:
                value = base64.b64decode(protobuf_bytes)
            except Exception as e:
                raise TypeError(
                    f"Expected bytes or base64-encoded string, got {type(protobuf_bytes).__name__}. Error: {str(e)}",
                ) from e

        # Create message instance and deserialize
        message = message_class()
        message.ParseFromString(value)

        # Convert to dictionary
        return MessageToDict(message, preserving_proto_field_name=True)

    except Exception as e:
        raise KafkaConsumerDeserializationError(
            f"Protocol Buffer deserialization error: {type(e).__name__}: {str(e)}",
        ) from e
