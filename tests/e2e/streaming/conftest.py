import pytest

from tests.e2e.streaming.infrastructure import StreamingStack


@pytest.fixture(autouse=True, scope="module")
def infrastructure(tmp_path_factory, worker_id):
    """Setup and teardown logic for E2E test infrastructure

    Yields
    ------
    Dict[str, str]
        CloudFormation Outputs from deployed infrastructure
    """
    stack = StreamingStack()
    try:
        yield stack.deploy()
    finally:
        stack.delete()
