import pytest


@pytest.fixture(autouse=True, scope="package")
def infrastructure():
    """Setup and teardown logic for E2E test infrastructure

    Yields
    ------
    Dict[str, str]
        CloudFormation Outputs from deployed infrastructure
    """

    return None

    # MAINTENANCE: Uncomment the code below to enable Redis e2e tests when dropping Python 3.7
    """
    stack = IdempotencyRedisServerlessStack()
    try:
        yield stack.deploy()
    finally:
        stack.delete()
    """
