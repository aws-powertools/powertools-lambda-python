from pathlib import Path

import pytest

from tests.e2e.metrics.infrastructure import MetricsStack


@pytest.fixture(autouse=True, scope="module")
def infrastructure(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
    worker_id: str,
    lambda_layer_deployment: dict,
):
    """Setup and teardown logic for E2E test infrastructure

    Parameters
    ----------
    request : pytest.FixtureRequest
        pytest request fixture to introspect absolute path to test being executed
    tmp_path_factory : pytest.TempPathFactory
        pytest temporary path factory to discover shared tmp when multiple CPU processes are spun up
    worker_id : str
        pytest-xdist worker identification to detect whether parallelization is enabled

    Yields
    ------
    Dict[str, str]
        CloudFormation Outputs from deployed infrastructure
    """
    layer_arn = lambda_layer_deployment.get("LayerArn")
    stack = MetricsStack(handlers_dir=Path(f"{request.path.parent}/handlers"), layer_arn=layer_arn)
    try:
        yield stack.deploy()
    finally:
        stack.delete()
