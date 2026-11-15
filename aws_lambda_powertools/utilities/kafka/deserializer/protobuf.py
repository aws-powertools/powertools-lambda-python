from __future__ import annotations

import logging
from typing import Any

from google.protobuf.internal.decoder import (  # type: ignore[attr-defined]
    _DecodeVarint,  # ty: ignore[unresolved-import]
)
from google.protobuf.json_format import MessageToDict

from aws_lambda_powertools.utilities.kafka.deserializer.base import DeserializerBase
from aws_lambda_powertools.utilities.kafka.exceptions import (
    KafkaConsumerDeserializationError,
    KafkaConsumerDeserializationFormatMismatch,
)

logger = logging.getLogger(__name__)


class ProtobufDeserializer(DeserializerBase):
    """
    Deserializer for Protocol Buffer formatted data.

    This class provides functionality to deserialize Protocol Buffer binary data
    into Python dictionaries using the provided Protocol Buffer message class.
    """

    def __init__(self, message_class: Any, field_metadata: dict[str, Any] | None = None):
        self.message_class = message_class
        self.field_metatada = field_metadata

    def deserialize(self, data: bytes | str) -> dict:
        """
        Deserialize Protocol Buffer binary data to a Python dictionary.

        Parameters
        ----------
        data : bytes or str
            The Protocol Buffer binary data to deserialize. If provided as a string,
            it's assumed to be base64-encoded and will be decoded first.

        Returns
        -------
        dict
            Deserialized data as a dictionary with field names preserved from the
            Protocol Buffer definition.

        Raises
        ------
        KafkaConsumerDeserializationError
            When the data cannot be deserialized according to the message class,
            typically due to data format incompatibility or incorrect message class.

        Notes
        -----
        This deserializer handles both standard Protocol Buffer format and the Confluent
        Schema Registry format which includes message index information. It will first try
        standard deserialization and fall back to message index handling if needed.

        Example
        --------
        >>> # Assuming proper protobuf setup
        >>> deserializer = ProtobufDeserializer(my_proto_module.MyMessage)
        >>> proto_data = b'...'  # binary protobuf data
        >>> try:
        ...     result = deserializer.deserialize(proto_data)
        ...     # Process the deserialized dictionary
        ... except KafkaConsumerDeserializationError as e:
        ...     print(f"Failed to deserialize: {e}")
        """

        data_format = self.field_metatada.get("dataFormat") if self.field_metatada else None
        schema_id = self.field_metatada.get("schemaId") if self.field_metatada else None

        if data_format and data_format != "PROTOBUF":
            raise KafkaConsumerDeserializationFormatMismatch(f"Expected data is PROTOBUF but you sent {data_format}")

        logger.debug("Deserializing data with PROTOBUF format")

        try:
            value = self._decode_input(data)
            message = self.message_class()
            if schema_id is None:
                logger.debug("Plain PROTOBUF data: using default deserializer")
                # Plain protobuf - direct parser
                message.ParseFromString(value)
            elif len(schema_id) > 20:
                logger.debug("PROTOBUF data integrated with Glue SchemaRegistry: using Glue deserializer")
                # Glue schema registry integration - remove the first byte
                message.ParseFromString(value[1:])
            else:
                logger.debug("PROTOBUF data integrated with Confluent SchemaRegistry: using Confluent deserializer")
                # Confluent schema registry integration - remove message index list
                message.ParseFromString(self._remove_message_index(value))

            return MessageToDict(message, preserving_proto_field_name=True)
        except Exception as e:
            raise KafkaConsumerDeserializationError(
                f"Error trying to deserialize protobuf data - {type(e).__name__}: {str(e)}",
            ) from e

    def _remove_message_index(self, data):
        """
        Identifies and removes Confluent Schema Registry MessageIndex from bytes.
        Returns pure protobuf bytes.

        Confluent serializers write the message index array as zigzag encoded varints:
        the array length followed by each index. The common case, index ``[0]``, is a single ``0x00`` byte.
        This matches ``_encode_varints`` / ``_read_index_array`` in ``confluent_kafka.schema_registry.protobuf``.
        """
        buffer = memoryview(data)

        logger.debug("Removing message list bytes")

        # Read the number of indexes (0 means the first message type in the schema)
        count, pos = _decode_zigzag_varint(buffer, 0)
        if count < 0:
            raise ValueError(f"Invalid Confluent message index array length: {count}")

        # Skip index values if present
        for _ in range(count):
            _, pos = _decode_zigzag_varint(buffer, pos)

        # Return remaining bytes (pure protobuf)
        return data[pos:]


def _decode_zigzag_varint(buffer: memoryview, pos: int) -> tuple[int, int]:
    """Decode a zigzag encoded varint, as used by Confluent for message indexes."""
    value, new_pos = _DecodeVarint(buffer, pos)
    return (value >> 1) ^ -(value & 1), new_pos
