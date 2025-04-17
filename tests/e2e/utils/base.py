from __future__ import annotations

from abc import ABC, abstractmethod


class InfrastructureProvider(ABC):
    @abstractmethod
    def create_lambda_functions(self, function_props: dict | None = None) -> dict:
        pass

    @abstractmethod
    def deploy(self) -> dict[str, str]:
        pass

    @abstractmethod
    def delete(self):
        pass

    @abstractmethod
    def create_resources(self):
        pass
