import pytest

from tests.e2e.metrics.infrastructure import MetricsStack


@pytest.fixture(autouse=True)
def setup_infra():
    try:
        stack = MetricsStack()
        yield stack.deploy()
    finally:
        stack.delete()
