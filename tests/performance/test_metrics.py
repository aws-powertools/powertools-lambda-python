import time
from contextlib import contextmanager
from typing import Dict, Generator

import pytest

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.metrics import metrics as metrics_global

METRICS_VALIDATION_SLA: float = 0.01
METRICS_SERIALIZATION_SLA: float = 0.01


@contextmanager
def timing() -> Generator:
    """ "Generator to quickly time operations. It can add 5ms so take that into account in elapsed time

    Examples
    --------

        with timing() as t:
            print("something")
        elapsed = t()
    """
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start  # gen as lambda to calculate elapsed time


@pytest.fixture(scope="function", autouse=True)
def reset_metric_set():
    metrics = Metrics()
    metrics.clear_metrics()
    metrics_global.is_cold_start = True  # ensure each test has cold start
    yield


@pytest.fixture
def namespace() -> str:
    return "test_namespace"


@pytest.fixture
def metric() -> Dict[str, str]:
    return {"name": "single_metric", "unit": MetricUnit.Count, "value": 1}


def time_large_metric_set_operation(metrics_instance: Metrics, validate_metrics: bool = True) -> float:
    metrics_instance.add_dimension(name="test_dimension", value="test")

    for i in range(99):
        metrics_instance.add_metric(name=f"metric_{i}", unit="Count", value=1)

    with timing() as t:
        metrics_instance.serialize_metric_set(validate_metrics=validate_metrics)

    return t()


@pytest.mark.perf
def test_metrics_validation_sla(namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(namespace=namespace)
    # WHEN we add and serialize 99 metrics
    elapsed = time_large_metric_set_operation(metrics_instance=my_metrics)

    # THEN completion time should be below our validation SLA
    if elapsed > METRICS_VALIDATION_SLA:
        pytest.fail(f"Metric validation should be below {METRICS_VALIDATION_SLA}s: {elapsed}")


@pytest.mark.perf
def test_metrics_serialization_sla(namespace):
    # GIVEN Metrics is initialized with validation disabled
    my_metrics = Metrics(namespace=namespace, validate_metrics=False)
    # WHEN we add and serialize 99 metrics
    elapsed = time_large_metric_set_operation(metrics_instance=my_metrics, validate_metrics=False)

    # THEN completion time should be below our serialization SLA
    if elapsed > METRICS_SERIALIZATION_SLA:
        pytest.fail(f"Metric serialization should be below {METRICS_SERIALIZATION_SLA}s: {elapsed}")
