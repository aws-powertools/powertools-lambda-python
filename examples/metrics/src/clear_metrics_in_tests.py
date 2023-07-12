import pytest

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import metrics as metrics_global


@pytest.fixture(scope="function", autouse=True)
def reset_metric_set():
    # Clear out every metric data prior to every test
    metrics = Metrics()
    metrics.clear_metrics()
    metrics_global.is_cold_start = True  # ensure each test has cold start
    metrics.clear_default_dimensions()  # remove persisted default dimensions, if any
    yield
