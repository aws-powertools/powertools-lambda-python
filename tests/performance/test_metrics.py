import json
import time
from contextlib import contextmanager
from typing import Dict, Generator

import pytest

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.metrics import metrics as metrics_global

# adjusted for slower machines in CI too
METRICS_VALIDATION_SLA: float = 0.002
METRICS_SERIALIZATION_SLA: float = 0.002


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


def add_max_metrics_before_serialization(metrics_instance: Metrics):
    metrics_instance.add_dimension(name="test_dimension", value="test")

    for i in range(99):
        metrics_instance.add_metric(name=f"metric_{i}", unit="Count", value=1)


@pytest.mark.perf
def test_metrics_large_operation_without_json_serialization_sla(namespace):
    # GIVEN Metrics is initialized
    my_metrics = Metrics(namespace=namespace)

    # WHEN we add and serialize 99 metrics
    with timing() as t:
        add_max_metrics_before_serialization(metrics_instance=my_metrics)
        my_metrics.serialize_metric_set()

    # THEN completion time should be below our validation SLA
    elapsed = t()
    if elapsed > METRICS_VALIDATION_SLA:
        pytest.fail(f"Metric validation should be below {METRICS_VALIDATION_SLA}s: {elapsed}")


@pytest.mark.perf
def test_metrics_large_operation_and_json_serialization_sla(namespace):
    # GIVEN Metrics is initialized with validation disabled
    my_metrics = Metrics(namespace=namespace)

    # WHEN we add and serialize 99 metrics
    with timing() as t:
        add_max_metrics_before_serialization(metrics_instance=my_metrics)
        metrics = my_metrics.serialize_metric_set()
        print(json.dumps(metrics, separators=(",", ":")))

    # THEN completion time should be below our serialization SLA
    elapsed = t()
    if elapsed > METRICS_SERIALIZATION_SLA:
        pytest.fail(f"Metric serialization should be below {METRICS_SERIALIZATION_SLA}s: {elapsed}")
