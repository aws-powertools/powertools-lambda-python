"""CDK infrastructure for OpenTelemetry Tracer E2E tests."""

from __future__ import annotations

from tests.e2e.utils.infrastructure import BaseInfrastructure


class TracerOtelStack(BaseInfrastructure):
    """Infrastructure stack for OpenTelemetry Tracer E2E tests.

    Deploys Lambda functions with ADOT Layer for testing auto and manual modes.
    """

    # ADOT Lambda Layer ARN (update version as needed)
    ADOT_LAYER_ARN = "arn:aws:lambda:{region}:901920570463:layer:aws-otel-python-amd64-ver-1-24-0:1"

    def create_resources(self) -> None:
        self.create_lambda_functions()
