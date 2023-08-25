"""
Serialization for supporting idempotency
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseIdempotencySerializer(ABC):
    """
    Abstract Base Class for Idempotency serialization layer, supporting dict operations.
    """

    @abstractmethod
    def to_dict(self, data: Any) -> Dict:
        pass

    @abstractmethod
    def from_dict(self, data: Dict) -> Any:
        pass
