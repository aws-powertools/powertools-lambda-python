from __future__ import annotations

from typing import Any

from aws_lambda_powertools.utilities.kafka_consumer.deserializer.base import DeserializerBase


class NoOpDeserializer(DeserializerBase):
    """
    A pass-through deserializer that performs no transformation on the input data.

    This deserializer simply returns the input data unchanged, which is useful when
    no deserialization is needed or when handling raw data formats.
    """

    def deserialize(self, data: bytes | str) -> dict[str, Any]:
        """
        Return the input data unchanged.

        This method implements the deserialize interface but performs no transformation,
        simply returning the input data as-is.

        Parameters
        ----------
        data : bytes or str
            The input data to "deserialize".

        Returns
        -------
        dict[str, Any]
            The input data unchanged. Note that despite the type annotation,
            this method returns the exact same object that was passed in,
            preserving its original type.

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
        return data
