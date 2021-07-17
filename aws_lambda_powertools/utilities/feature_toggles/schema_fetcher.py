from abc import ABC, abstractclassmethod
from typing import Any, Dict


class SchemaFetcher(ABC):
    def __init__(self, configuration_name: str, cache_seconds: int):
        self.configuration_name = configuration_name
        self._cache_seconds = cache_seconds

    @abstractclassmethod
    def get_json_configuration(self) -> Dict[str, Any]:
        """Get configuration string from any configuration storing service and return the parsed JSON dictionary

        Raises:
            ConfigurationException: Any error that can occur during schema fetch or JSON parse

        Returns:
            Dict[str, Any]: parsed JSON dictionary
        """
        return None
