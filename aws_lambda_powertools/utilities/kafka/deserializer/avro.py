from __future__ import annotations

import io
import logging
from typing import Any, Literal

from avro.io import BinaryDecoder, DatumReader
from avro.schema import parse as parse_schema

from aws_lambda_powertools.utilities.kafka.deserializer.base import DeserializerBase
from aws_lambda_powertools.utilities.kafka.exceptions import (
    KafkaConsumerAvroSchemaParserError,
    KafkaConsumerDeserializationError,
    KafkaConsumerDeserializationFormatMismatch,
)

logger = logging.getLogger(__name__)

_CONFLUENT_HEADER_SIZE = 5
_CONFLUENT_MAGIC_BYTE = 0x00


class AvroDeserializer(DeserializerBase):
    """
    Deserializer for Apache Avro formatted data.

    This class provides functionality to deserialize Avro binary data using
    a provided Avro schema definition.
    """

    def __init__(
        self,
        schema_str: str,
        field_metadata: dict[str, Any] | None = None,
        wire_format: Literal["CONFLUENT"] | None = None,
    ):
        try:
            self.parsed_schema = parse_schema(schema_str)
            self.reader = DatumReader(self.parsed_schema)
            self.field_metatada = field_metadata
            self.wire_format = wire_format
        except Exception as e:
            raise KafkaConsumerAvroSchemaParserError(
                f"Invalid Avro schema. Please ensure the provided avro schema is valid: {type(e).__name__}: {str(e)}",
            ) from e

    def _strip_wire_format_header(self, value: bytes) -> bytes:
        if self.wire_format is None:
            return value

        if self.wire_format != "CONFLUENT":
            raise KafkaConsumerDeserializationError(f"Unsupported Avro wire format: {self.wire_format}")

        if len(value) < _CONFLUENT_HEADER_SIZE:
            raise KafkaConsumerDeserializationError(
                "Invalid Confluent wire format: payload must contain a 5-byte header",
            )

        if value[0] != _CONFLUENT_MAGIC_BYTE:
            raise KafkaConsumerDeserializationError(
                "Invalid Confluent wire format: expected magic byte 0x00",
            )

        schema_id = int.from_bytes(value[1:_CONFLUENT_HEADER_SIZE], byteorder="big")
        logger.debug("Deserializing Confluent payload with schema ID %s", schema_id)
        return value[_CONFLUENT_HEADER_SIZE:]

    def deserialize(self, data: bytes | str) -> object:
        """
        Deserialize Avro binary data to a Python dictionary.

        Parameters
        ----------
        data : bytes or str
            The Avro binary data to deserialize. If provided as a string,
            it will be decoded to bytes first.

        Returns
        -------
        dict[str, Any]
            Deserialized data as a dictionary.

        Raises
        ------
        KafkaConsumerDeserializationError
            When the data cannot be deserialized according to the schema,
            typically due to data format incompatibility.

        Examples
        --------
        >>> deserializer = AvroDeserializer(schema_str)
        >>> avro_data = b'...'  # binary Avro data
        >>> try:
        ...     result = deserializer.deserialize(avro_data)
        ...     # Process the deserialized data
        ... except KafkaConsumerDeserializationError as e:
        ...     print(f"Failed to deserialize: {e}")
        """
        data_format = self.field_metatada.get("dataFormat") if self.field_metatada else None

        if data_format and data_format != "AVRO":
            raise KafkaConsumerDeserializationFormatMismatch(f"Expected data is AVRO but you sent {data_format}")

        logger.debug("Deserializing data with AVRO format")

        try:
            value = self._decode_input(data)
            value = self._strip_wire_format_header(value)
            bytes_reader = io.BytesIO(value)
            decoder = BinaryDecoder(bytes_reader)
            return self.reader.read(decoder)
        except KafkaConsumerDeserializationError:
            raise
        except Exception as e:
            raise KafkaConsumerDeserializationError(
                f"Error trying to deserialize avro data - {type(e).__name__}: {str(e)}",
            ) from e
