from __future__ import annotations

import base64
import logging

from aws_lambda_powertools.utilities.kafka.deserializer.base import DeserializerBase

logger = logging.getLogger(__name__)


class DefaultDeserializer(DeserializerBase):
    """
    A default deserializer that performs base64 decode + binary decode on the input data.

    This deserializer simply returns the input data with base64 decode, which is useful when
    no customized deserialization is needed or when handling raw data formats.
    """

    def deserialize(self, data: bytes | str) -> str:
        """
        Return the input data base64 decoded.

        This method implements the deserialize interface and performs base64 decode.

        Parameters
        ----------
        data : bytes or str
            The input data to "deserialize".

        Returns
        -------
        dict[str, Any]
            The input data base64 decoded.

        Example
        --------
        >>> deserializer = NoOpDeserializer()
        >>>
        >>> # With string input
        >>> string_data = "Hello, world!"
        >>> result = deserializer.deserialize(string_data)
        >>> print(result == string_data)  # Output: True
        >>>
        >>> # With bytes input
        >>> bytes_data = b"Binary data"
        >>> result = deserializer.deserialize(bytes_data)
        >>> print(result == bytes_data)  # Output: True
        """
        logger.debug("Deserializing data with primitives types")
        return base64.b64decode(data).decode("utf-8")
