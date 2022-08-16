from pathlib import Path

from tests.e2e.utils.infrastructure import BaseInfrastructureV2


class TracerStack(BaseInfrastructureV2):
    def __init__(self, handlers_dir: Path, feature_name: str = "tracer") -> None:
        super().__init__(feature_name, handlers_dir)

    def create_resources(self):
        self.create_lambda_functions()
