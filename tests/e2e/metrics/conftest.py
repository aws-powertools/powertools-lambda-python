import pytest

from tests.e2e.metrics.infrastructure import MetricsStack


@pytest.fixture(autouse=True)
def infrastructure() -> MetricsStack:
    # Use request fixture to remove hardcode handler dir
    try:
        stack = MetricsStack()
        stack.deploy()
        yield stack
    finally:
        stack.delete()
