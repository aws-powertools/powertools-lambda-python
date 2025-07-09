from __future__ import annotations

import logging
from typing import Any

from google.protobuf.internal.decoder import _DecodeSignedVarint  # type: ignore[attr-defined]
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
        """
        buffer = memoryview(data)
        pos = 0

        logger.debug("Removing message list bytes")

        # Read first varint (index count or 0)
        first_value, new_pos = _DecodeSignedVarint(buffer, pos)
        pos = new_pos

        # Skip index values if present
        if first_value != 0:
            for _ in range(first_value):
                _, new_pos = _DecodeSignedVarint(buffer, pos)
                pos = new_pos

        # Return remaining bytes (pure protobuf)
        return data[pos:]
