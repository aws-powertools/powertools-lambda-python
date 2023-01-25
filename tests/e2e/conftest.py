import pytest

from tests.e2e.utils.infrastructure import call_once
from tests.e2e.utils.lambda_layer.powertools_layer import LocalLambdaPowertoolsLayer


@pytest.fixture(scope="session", autouse=True)
def lambda_layer_build(tmp_path_factory: pytest.TempPathFactory, worker_id: str) -> str:
    """Build Lambda Layer once before stacks are created

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        pytest temporary path factory to discover shared tmp when multiple CPU processes are spun up
    worker_id : str
        pytest-xdist worker identification to detect whether parallelization is enabled

    Yields
    ------
    str
        Lambda Layer artefact location
    """

    layer = LocalLambdaPowertoolsLayer()
    yield from call_once(
        task=layer.build,
        tmp_path_factory=tmp_path_factory,
        worker_id=worker_id,
    )
