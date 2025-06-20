from __future__ import annotations

import base64
import json
import logging
from typing import Any

from aws_lambda_powertools.utilities.kafka.deserializer.base import DeserializerBase
from aws_lambda_powertools.utilities.kafka.exceptions import (
    KafkaConsumerDeserializationError,
    KafkaConsumerDeserializationFormatMismatch,
)

logger = logging.getLogger(__name__)


class JsonDeserializer(DeserializerBase):
    """
    Deserializer for JSON formatted data.

    This class provides functionality to deserialize JSON data from bytes or string
    into Python dictionaries.
    """

    def __init__(self, field_metadata: dict[str, Any] | None = None):
        self.field_metatada = field_metadata

    def deserialize(self, data: bytes | str) -> dict:
        """
        Deserialize JSON data to a Python dictionary.

        Parameters
        ----------
        data : bytes or str
            The JSON data to deserialize. If provided as bytes, it will be decoded as UTF-8.
            If provided as a string, it's assumed to be base64-encoded and will be decoded first.

        Returns
        -------
        dict
            Deserialized data as a dictionary.

        Raises
        ------
        KafkaConsumerDeserializationError
            When the data cannot be deserialized as valid JSON.

        Examples
        --------
        >>> deserializer = JsonDeserializer()
        >>> json_data = '{"key": "value", "number": 123}'
        >>> try:
        ...     result = deserializer.deserialize(json_data)
        ...     print(result["key"])  # Output: value
        ... except KafkaConsumerDeserializationError as e:
        ...     print(f"Failed to deserialize: {e}")
        """

        data_format = self.field_metatada.get("dataFormat") if self.field_metatada else None

        if data_format and data_format != "JSON":
            raise KafkaConsumerDeserializationFormatMismatch(f"Expected data is JSON but you sent {data_format}")

        logger.debug("Deserializing data with JSON format")

        try:
            return json.loads(base64.b64decode(data).decode("utf-8"))
        except Exception as e:
            raise KafkaConsumerDeserializationError(
                f"Error trying to deserialize json data -  {type(e).__name__}: {str(e)}",
            ) from e
