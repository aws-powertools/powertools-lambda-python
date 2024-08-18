from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StoreProvider(ABC):
    @property
    @abstractmethod
    def get_raw_configuration(self) -> dict[str, Any]:
        """Get configuration from any store and return the parsed JSON dictionary"""
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def get_configuration(self) -> dict[str, Any]:
        """Get configuration from any store and return the parsed JSON dictionary

        If envelope is set, it'll extract and return feature flags from configuration,
        otherwise it'll return the entire configuration fetched from the store.

        Raises
        ------
        ConfigurationStoreError
            Any error that can occur during schema fetch or JSON parse

        Returns
        -------
        dict[str, Any]
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
        raise NotImplementedError()  # pragma: no cover


class BaseValidator(ABC):
    @abstractmethod
    def validate(self):
        raise NotImplementedError()  # pragma: no cover
