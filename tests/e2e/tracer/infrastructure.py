from pathlib import Path

from tests.e2e.utils.data_builder import build_service_name
from tests.e2e.utils.infrastructure import BaseInfrastructureV2


class TracerStack(BaseInfrastructureV2):
    # Maintenance: Tracer doesn't support dynamic service injection (tracer.py L310)
    # we could move after handler response or adopt env vars usage in e2e tests
    SERVICE_NAME: str = build_service_name()

    def __init__(self, handlers_dir: Path, feature_name: str = "tracer", layer_arn: str = "") -> None:
        super().__init__(feature_name, handlers_dir, layer_arn)

    def create_resources(self) -> None:
        env_vars = {"POWERTOOLS_SERVICE_NAME": self.SERVICE_NAME}
        self.create_lambda_functions(function_props={"environment": env_vars})
