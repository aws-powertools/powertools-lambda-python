import json
from pathlib import Path
from typing import Dict

import pytest
from _pytest import fixtures
from filelock import FileLock

from tests.e2e.metrics.infrastructure import MetricsStack


@pytest.fixture(autouse=True, scope="module")
def infrastructure(request: fixtures.SubRequest, tmp_path_factory: pytest.TempPathFactory, worker_id) -> MetricsStack:
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
    stack = MetricsStack(handlers_dir=Path(f"{request.fspath.dirname}/handlers"))
    try:
        if worker_id == "master":
            # no parallelization, deploy stack and let fixture be cached
            yield stack.deploy()

        # tmp dir shared by all workers
        root_tmp_dir = tmp_path_factory.getbasetemp().parent

        cache = root_tmp_dir / "cache.json"
        with FileLock(f"{cache}.lock"):
            # If cache exists, return stack outputs back
            # otherwise it's the first run by the main worker
            # deploy and return stack outputs so subsequent workers can reuse
            if cache.is_file():
                stack_outputs = json.loads(cache.read_text())
            else:
                stack_outputs: Dict = stack.deploy()
                cache.write_text(json.dumps(stack_outputs))
        yield stack_outputs
    finally:
        stack.delete()
