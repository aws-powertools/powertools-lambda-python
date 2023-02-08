import json

import pytest

from tests.e2e.utils import data_builder, data_fetcher


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


@pytest.mark.xdist_group(name="metrics")
def test_basic_lambda_metric_is_visible(basic_handler_fn: str, basic_handler_fn_arn: str):
    # GIVEN
    metric_name = data_builder.build_metric_name()
    service = data_builder.build_service_name()
    dimensions = data_builder.build_add_dimensions_input(service=service)
    metrics = data_builder.build_multiple_add_metric_input(metric_name=metric_name, value=1, quantity=3)

    # WHEN
    event = json.dumps({"metrics": metrics, "service": service, "namespace": METRIC_NAMESPACE})
    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn, payload=event)

    metric_values = data_fetcher.get_metrics(
        namespace=METRIC_NAMESPACE, start_date=execution_time, metric_name=metric_name, dimensions=dimensions
    )

    # THEN
    assert metric_values == [3.0]


@pytest.mark.xdist_group(name="metrics")
def test_cold_start_metric(cold_start_fn_arn: str, cold_start_fn: str):
    # GIVEN
    metric_name = "ColdStart"
    service = data_builder.build_service_name()
    dimensions = data_builder.build_add_dimensions_input(function_name=cold_start_fn, service=service)

    # WHEN we invoke twice
    event = json.dumps({"service": service, "namespace": METRIC_NAMESPACE})

    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=cold_start_fn_arn, payload=event)
    data_fetcher.get_lambda_response(lambda_arn=cold_start_fn_arn, payload=event)

    metric_values = data_fetcher.get_metrics(
        namespace=METRIC_NAMESPACE, start_date=execution_time, metric_name=metric_name, dimensions=dimensions
    )

    # THEN
    assert metric_values == [1.0]
