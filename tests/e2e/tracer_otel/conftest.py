"""E2E test fixtures for OpenTelemetry Tracer."""

import pytest


@pytest.fixture
def infrastructure():
    """Fixture to deploy and teardown test infrastructure."""
    # Infrastructure deployment handled by CDK in infrastructure.py
    pass
