import pytest

from tests.e2e.metrics.infrastructure import MetricsStack
from tests.e2e.utils.infrastructure import deploy_once


@pytest.fixture(autouse=True, scope="module")
def infrastructure(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory, worker_id: str):
    """Setup and teardown logic for E2E test infrastructure

    Parameters
    ----------
    request : fixtures.SubRequest
        test fixture containing metadata about test execution

    Yields
    ------
    Dict[str, str]
        CloudFormation Outputs from deployed infrastructure
    """
    yield from deploy_once(stack=MetricsStack, request=request, tmp_path_factory=tmp_path_factory, worker_id=worker_id)
