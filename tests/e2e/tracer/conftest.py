from pathlib import Path

import pytest

from tests.e2e.tracer.infrastructure import TracerStack


@pytest.fixture(autouse=True, scope="module")
# NOTE: Commented out for faster debug as we don't need a Layer yet
# def infrastructure(request: pytest.FixtureRequest, lambda_layer_arn: str):
def infrastructure(request: pytest.FixtureRequest):
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
    # NOTE: Commented out for faster debug as we don't need a Layer yet
    # stack = TracerStack(handlers_dir=Path(f"{request.path.parent}/handlers"), layer_arn=lambda_layer_arn)
    stack = TracerStack(handlers_dir=Path(f"{request.path.parent}/handlers"), layer_arn="")
    try:
        yield stack.deploy()
    finally:
        stack.delete()
