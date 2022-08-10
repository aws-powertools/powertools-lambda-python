from pathlib import Path

import pytest
from _pytest import fixtures

from tests.e2e.metrics.infrastructure import MetricsStack


@pytest.fixture(autouse=True)
def infrastructure(request: fixtures.SubRequest) -> MetricsStack:
    """Setup and teardown logic for E2E test infrastructure

    Parameters
    ----------
    request : fixtures.SubRequest
        test fixture containing metadata about test execution

    Returns
    -------
    MetricsStack
        Metrics Stack to deploy infrastructure

    Yields
    ------
    Iterator[MetricsStack]
        Deployed Infrastructure
    """
    try:
        stack = MetricsStack(handlers_dir=Path(f"{request.fspath.dirname}/handlers"))
        stack.deploy()
        yield stack
    finally:
        stack.delete()
