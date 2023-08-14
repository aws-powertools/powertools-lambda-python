import pytest

from aws_lambda_powertools.metrics.provider import cold_start
from aws_lambda_powertools.metrics.provider.datadog import DatadogMetrics


@pytest.fixture(scope="function", autouse=True)
def reset_metric_set():
    # Clear out every metric data prior to every test
    metrics = DatadogMetrics()
    metrics.clear_metrics()
    cold_start.is_cold_start = True  # ensure each test has cold start
    yield
