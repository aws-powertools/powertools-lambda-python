from pathlib import Path

from tests.e2e.utils.data_builder import build_service_name
from tests.e2e.utils.infrastructure import BaseInfrastructure

PWD = Path(__file__).parent


class TracerStack(BaseInfrastructure):
    # Maintenance: Tracer doesn't support dynamic service injection (tracer.py L310)
    # we could move after handler response or adopt env vars usage in e2e tests
    SERVICE_NAME: str = build_service_name()
    FEATURE_NAME = "tracer"

    def __init__(self, feature_name: str = FEATURE_NAME) -> None:
        super().__init__(feature_name)

    def create_resources(self) -> None:
        # NOTE: Commented out Lambda fns as we don't need them now
        env_vars = {"POWERTOOLS_SERVICE_NAME": self.SERVICE_NAME}
        self.create_lambda_functions(function_props={"environment": env_vars})
