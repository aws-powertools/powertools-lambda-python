from __future__ import annotations

from typing import Any

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
        try:
            value = self._decode_input(data)
            message = self.message_class()
            message.ParseFromString(value)
            return MessageToDict(message, preserving_proto_field_name=True)
        except Exception as e:
            raise KafkaConsumerDeserializationError(
                f"Error trying to deserialize protobuf data - {type(e).__name__}: {str(e)}",
            ) from e
