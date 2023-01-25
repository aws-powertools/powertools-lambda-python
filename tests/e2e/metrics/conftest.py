import pytest

from tests.e2e.metrics.infrastructure import MetricsStack


@pytest.fixture(autouse=True, scope="package")
def infrastructure():
    """Setup and teardown logic for E2E test infrastructure

    Yields
    ------
    Dict[str, str]
        CloudFormation Outputs from deployed infrastructure
    """
    stack = MetricsStack()
    try:
        yield stack.deploy()
    finally:
        stack.delete()
