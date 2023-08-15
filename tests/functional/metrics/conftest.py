from typing import Any, Dict, List, Union

import pytest

from aws_lambda_powertools.metrics import (
    MetricResolution,
    Metrics,
    MetricUnit,
)
from aws_lambda_powertools.metrics.provider.cold_start import reset_cold_start_flag


@pytest.fixture(scope="function", autouse=True)
def reset_metric_set():
    metrics = Metrics()
    metrics.clear_metrics()
    metrics.clear_default_dimensions()
    reset_cold_start_flag()  # ensure each test has cold start
    yield


@pytest.fixture
def metric_with_resolution() -> Dict[str, Union[str, int]]:
    return {"name": "single_metric", "unit": MetricUnit.Count, "value": 1, "resolution": MetricResolution.High}


@pytest.fixture
def metric() -> Dict[str, str]:
    return {"name": "single_metric", "unit": MetricUnit.Count, "value": 1}


@pytest.fixture
def metric_datadog() -> Dict[str, str]:
    return {"name": "single_metric", "value": 1, "timestamp": 1691678198, "powertools": "datadog"}


@pytest.fixture
def metrics() -> List[Dict[str, str]]:
    return [
        {"name": "metric_one", "unit": MetricUnit.Count, "value": 1},
        {"name": "metric_two", "unit": MetricUnit.Count, "value": 1},
    ]


@pytest.fixture
def metrics_same_name() -> List[Dict[str, str]]:
    return [
        {"name": "metric_one", "unit": MetricUnit.Count, "value": 1},
        {"name": "metric_one", "unit": MetricUnit.Count, "value": 5},
    ]


@pytest.fixture
def dimension() -> Dict[str, str]:
    return {"name": "test_dimension", "value": "test"}


@pytest.fixture
def dimensions() -> List[Dict[str, str]]:
    return [
        {"name": "test_dimension", "value": "test"},
        {"name": "test_dimension_2", "value": "test"},
    ]


@pytest.fixture
def non_str_dimensions() -> List[Dict[str, Any]]:
    return [
        {"name": "test_dimension", "value": True},
        {"name": "test_dimension_2", "value": 3},
    ]


@pytest.fixture
def namespace() -> str:
    return "test_namespace"


@pytest.fixture
def service() -> str:
    return "test_service"


@pytest.fixture
def metadata() -> Dict[str, str]:
    return {"key": "username", "value": "test"}


@pytest.fixture
def a_hundred_metrics() -> List[Dict[str, str]]:
    return [{"name": f"metric_{i}", "unit": "Count", "value": 1} for i in range(100)]


@pytest.fixture
def a_hundred_metric_values() -> List[Dict[str, str]]:
    return [{"name": "metric", "unit": "Count", "value": i} for i in range(100)]
