from abc import ABC, abstractmethod
from typing import Dict, Optional


class InfrastructureProvider(ABC):
    @abstractmethod
    def create_lambda_functions(self, function_props: Optional[Dict] = None) -> Dict:
        pass

    @abstractmethod
    def deploy(self) -> Dict[str, str]:
        pass

    @abstractmethod
    def delete(self):
        pass

    @abstractmethod
    def create_resources(self):
        pass
