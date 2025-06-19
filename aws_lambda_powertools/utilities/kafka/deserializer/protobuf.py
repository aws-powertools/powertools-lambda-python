from __future__ import annotations

from typing import Any

from google.protobuf.internal.decoder import _DecodeVarint  # type: ignore[attr-defined]
from google.protobuf.json_format import MessageToDict

from aws_lambda_powertools.utilities.kafka.deserializer.base import DeserializerBase
from aws_lambda_powertools.utilities.kafka.exceptions import (
    KafkaConsumerDeserializationError,
)


class ProtobufDeserializer(DeserializerBase):
    """
    Deserializer for Protocol Buffer formatted data.

    This class provides functionality to deserialize Protocol Buffer binary data
    into Python dictionaries using the provided Protocol Buffer message class.
    """

    def __init__(self, message_class: Any):
        self.message_class = message_class

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
        value = self._decode_input(data)
        try:
            message = self.message_class()
            message.ParseFromString(value)
            return MessageToDict(message, preserving_proto_field_name=True)
        except Exception:
            return self._deserialize_with_message_index(value, self.message_class())

    def _deserialize_with_message_index(self, data: bytes, parser: Any) -> dict:
        """
        Deserialize protobuf message with Confluent message index handling.

        Parameters
        ----------
        data : bytes
            data
        parser : google.protobuf.message.Message
            Protobuf message instance to parse the data into

        Returns
        -------
        dict
            Dictionary representation of the parsed protobuf message with original field names

        Raises
        ------
        KafkaConsumerDeserializationError
            If deserialization fails

        Notes
        -----
        This method handles the special case of Confluent Schema Registry's message index
        format, where the message is prefixed with either a single 0 (for the first schema)
        or a list of schema indexes. The actual protobuf message follows these indexes.
        """

        buffer = memoryview(data)
        pos = 0

        try:
            first_value, new_pos = _DecodeVarint(buffer, pos)
            pos = new_pos

            if first_value != 0:
                for _ in range(first_value):
                    _, new_pos = _DecodeVarint(buffer, pos)
                    pos = new_pos

            parser.ParseFromString(data[pos:])
            return MessageToDict(parser, preserving_proto_field_name=True)
        except Exception as e:
            raise KafkaConsumerDeserializationError(
                f"Error trying to deserialize protobuf data - {type(e).__name__}: {str(e)}",
            ) from e
