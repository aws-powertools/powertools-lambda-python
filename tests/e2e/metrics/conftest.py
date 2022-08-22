from pathlib import Path

import pytest

from tests.e2e.metrics.infrastructure import MetricsStack


@pytest.fixture(autouse=True, scope="module")
def infrastructure(request: pytest.FixtureRequest, lambda_layer_arn: str):
    """Setup and teardown logic for E2E test infrastructure

    Parameters
    ----------
    request : pytest.FixtureRequest
        pytest request fixture to introspect absolute path to test being executed
    lambda_layer_arn : str
        Lambda Layer ARN

    Yields
    ------
    Dict[str, str]
        CloudFormation Outputs from deployed infrastructure
    """
    stack = MetricsStack(handlers_dir=Path(f"{request.path.parent}/handlers"), layer_arn=lambda_layer_arn)
    try:
        yield stack.deploy()
    finally:
        stack.delete()
