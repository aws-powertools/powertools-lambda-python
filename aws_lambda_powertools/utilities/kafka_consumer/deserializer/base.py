from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from typing import Any


class DeserializerBase(ABC):
    @abstractmethod
    def deserialize(self, data: bytes | str) -> dict[str, Any]:
        pass

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
