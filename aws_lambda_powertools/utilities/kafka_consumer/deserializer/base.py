from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from typing import Any, overload


class DeserializerBase(ABC):
    """
    Abstract base class for deserializers.

    This class defines the interface for all deserializers in the Kafka consumer utility
    and provides a common method for decoding input data.

    Methods
    -------
    deserialize(data)
        Abstract method that must be implemented by subclasses to deserialize data.
    _decode_input(data)
        Helper method to decode input data to bytes.

    Examples
    --------
    >>> class MyDeserializer(DeserializerBase):
    ...     def deserialize(self, data: bytes | str) -> dict[str, Any]:
    ...         value = self._decode_input(data)
    ...         # Custom deserialization logic here
    ...         return {"key": "value"}
    """

    @abstractmethod
    def deserialize(self, data: bytes | str) -> dict[str, Any] | str | object:
        """
        Deserialize input data to a Python dictionary.

        This abstract method must be implemented by subclasses to provide
        specific deserialization logic.

        Parameters
        ----------
        data : bytes or str
            The data to deserialize, either as bytes or as a string.

        Returns
        -------
        dict[str, Any]
            The deserialized data as a dictionary.
        """
        raise NotImplementedError("Subclasses must implement the deserialize method")

    def _decode_input(self, data: bytes | str) -> bytes:
        if isinstance(data, str):
            return base64.b64decode(data)
        elif isinstance(data, bytes):
            return data
        else:
            try:
                return base64.b64decode(data)
            except Exception as e:
                raise TypeError(
                    f"Expected bytes or base64-encoded string, got {type(data).__name__}. Error: {str(e)}",
                ) from e
