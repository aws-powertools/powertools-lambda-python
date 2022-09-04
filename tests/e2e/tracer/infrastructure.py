from tests.e2e.utils.infrastructure import BaseInfrastructure


class TracerStack(BaseInfrastructure):
    def create_resources(self) -> None:
        self.create_lambda_functions()
