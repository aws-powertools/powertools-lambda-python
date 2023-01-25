import pytest

from tests.e2e.logger.infrastructure import LoggerStack
from tests.e2e.utils.infrastructure import call_once


@pytest.fixture(autouse=True, scope="module")
def infrastructure(tmp_path_factory, worker_id):
    """Setup and teardown logic for E2E test infrastructure

    Yields
    ------
    Dict[str, str]
        CloudFormation Outputs from deployed infrastructure
    """
    stack = LoggerStack()
    try:
        return (
            yield from call_once(
                job_id=stack.feature_name,
                task=stack.deploy,
                tmp_path_factory=tmp_path_factory,
                worker_id=worker_id,
            )
        )
    finally:
        stack.delete()
