from abc import ABC, abstractmethod
from typing import Any, Dict


class SchemaFetcher(ABC):
    def __init__(self, configuration_name: str, cache_seconds: int):
        self.name = configuration_name
        self._cache_seconds = cache_seconds

    @abstractmethod
    def get_json_configuration(self) -> Dict[str, Any]:
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
