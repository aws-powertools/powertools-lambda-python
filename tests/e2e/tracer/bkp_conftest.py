import pytest

from tests.e2e.tracer.infrastructure import TracerStack


@pytest.fixture(autouse=True, scope="module")
def infrastructure(lambda_layer_arn: str):
    # # def infrastructure(request: pytest.FixtureRequest):
    """Setup and teardown logic for E2E test infrastructure

    Parameters
    ----------
    lambda_layer_arn : str
        Lambda Layer ARN

    Yields
    ------
    Dict[str, str]
        CloudFormation Outputs from deployed infrastructure
    """
    stack = TracerStack(layer_arn=lambda_layer_arn)
    try:
        yield stack.deploy()
    finally:
        stack.delete()
