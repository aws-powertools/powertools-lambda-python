from abc import ABC, abstractmethod
from typing import Any, Dict


class StoreProvider(ABC):
    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """Get configuration from any store and return the parsed JSON dictionary

        Raises
        ------
        ConfigurationStoreError
            Any error that can occur during schema fetch or JSON parse

        Returns
        -------
        Dict[str, Any]
            parsed JSON dictionary

            **Example**

        ```python
        {
            "premium_features": {
                "default": False,
                "rules": {
                    "customer tier equals premium": {
                        "when_match": True,
                        "conditions": [
                            {
                                "action": "EQUALS",
                                "key": "tier",
                                "value": "premium",
                            }
                        ],
                    }
                },
            },
            "feature_two": {
                "default": False
            }
        }
        ```
        """
        return NotImplemented  # pragma: no cover


class BaseValidator(ABC):
    @abstractmethod
    def validate(self):
        return NotImplemented  # pragma: no cover
