from pathlib import Path

from tests.e2e.utils.infrastructure import BaseInfrastructureV2


class LoggerStack(BaseInfrastructureV2):
    LOG_MESSAGE: str = "logger message test"
    LOG_LEVEL: str = "INFO"

    def __init__(self, handlers_dir: Path, feature_name: str = "logger") -> None:
        super().__init__(feature_name, handlers_dir)

    def create_resources(self):
        env_vars = {
            "MESSAGE": self.LOG_MESSAGE,
            "LOG_LEVEL": self.LOG_LEVEL,
            "ADDITIONAL_KEY": "extra_info",
        }
        self.create_lambda_functions(function_props={"environment": env_vars})
