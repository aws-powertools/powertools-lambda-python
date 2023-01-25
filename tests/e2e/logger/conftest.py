import pytest

from tests.e2e.logger.infrastructure import LoggerStack


@pytest.fixture(autouse=True, scope="package")
def infrastructure():
    """Setup and teardown logic for E2E test infrastructure

    Yields
    ------
    Dict[str, str]
        CloudFormation Outputs from deployed infrastructure
    """
    stack = LoggerStack()
    try:
        yield stack.deploy()
    finally:
        stack.delete()
