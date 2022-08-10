import json

import pytest

from tests.e2e.utils import helpers


@pytest.fixture
def basic_handler_fn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandler", "")


@pytest.fixture
def basic_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandlerArn", "")


@pytest.fixture
def cold_start_fn(infrastructure: dict) -> str:
    return infrastructure.get("ColdStart", "")


@pytest.fixture
def cold_start_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("ColdStartArn", "")


METRIC_NAMESPACE = "powertools-e2e-metric"


def test_basic_lambda_metric_is_visible(basic_handler_fn: str, basic_handler_fn_arn: str):
    # GIVEN
    metric_name = helpers.build_metric_name()
    service = helpers.build_service_name()
    dimensions = helpers.build_add_dimensions_input(service=service)
    metrics = helpers.build_multiple_add_metric_input(metric_name=metric_name, value=1, quantity=3)

    # WHEN
    event = json.dumps({"metrics": metrics, "service": service, "namespace": METRIC_NAMESPACE})
    _, execution_time = helpers.trigger_lambda(lambda_arn=basic_handler_fn_arn, payload=event)

    metrics = helpers.get_metrics(
        namespace=METRIC_NAMESPACE, start_date=execution_time, metric_name=metric_name, dimensions=dimensions
    )

    # THEN
    metric_data = metrics.get("Values", [])
    assert metric_data and metric_data[0] == 3.0


def test_cold_start_metric(cold_start_fn_arn: str, cold_start_fn: str):
    # GIVEN
    metric_name = "ColdStart"
    service = helpers.build_service_name()
    dimensions = helpers.build_add_dimensions_input(function_name=cold_start_fn, service=service)

    # WHEN
    event = json.dumps({"service": service, "namespace": METRIC_NAMESPACE})
    _, execution_time = helpers.trigger_lambda(lambda_arn=cold_start_fn_arn, payload=event)

    metrics = helpers.get_metrics(
        namespace=METRIC_NAMESPACE, start_date=execution_time, metric_name=metric_name, dimensions=dimensions
    )

    # THEN
    metric_data = metrics.get("Values", [])
    assert metric_data and metric_data[0] == 1.0


# helpers: adjust retries and wait to be much smaller
# helpers: make retry config adjustable
# Create separate Infra class so they can live side by side
