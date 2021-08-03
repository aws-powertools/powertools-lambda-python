from abc import ABC, abstractmethod
from typing import Any, Dict


class StoreProvider(ABC):
    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """Get configuration string from any configuration storing application and return the parsed JSON dictionary

        Raises
        ------
        ConfigurationError
            Any error that can occur during schema fetch or JSON parse

        Returns
        -------
        Dict[str, Any]
            parsed JSON dictionary
        """
        return NotImplemented  # pragma: no cover


class BaseValidator(ABC):
    @abstractmethod
    def validate(self):
        return NotImplemented  # pragma: no cover
