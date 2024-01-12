import pytest

from tests.e2e.idempotency_redis.infrastructure import IdempotencyRedisServerlessStack


@pytest.fixture(autouse=True, scope="package")
def infrastructure():
    """Setup and teardown logic for E2E test infrastructure

    Yields
    ------
    Dict[str, str]
        CloudFormation Outputs from deployed infrastructure
    """
    stack = IdempotencyRedisServerlessStack()
    try:
        yield stack.deploy()
    finally:
        stack.delete()
