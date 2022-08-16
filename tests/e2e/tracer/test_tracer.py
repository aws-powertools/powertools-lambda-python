import pytest

from tests.e2e.tracer.handlers import basic_handler
from tests.e2e.tracer.infrastructure import TracerStack
from tests.e2e.utils import data_fetcher, helpers


@pytest.fixture
def basic_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandlerArn", "")


@pytest.fixture
def basic_handler_fn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandler", "")


def test_lambda_handler_trace_is_visible(basic_handler_fn_arn: str, basic_handler_fn: str):
    # GIVEN
    handler_name = basic_handler.lambda_handler.__name__
    handler_subsegment = f"## {handler_name}"
    handler_metadata_key = f"{handler_name} response"
    trace_query = helpers.build_trace_default_query(function_name=basic_handler_fn)

    # WHEN
    _, execution_time = helpers.trigger_lambda(lambda_arn=basic_handler_fn_arn)
    helpers.trigger_lambda(lambda_arn=basic_handler_fn_arn)

    # THEN
    trace = data_fetcher.get_traces(start_date=execution_time, filter_expression=trace_query)

    assert len(trace.get_annotation(key="ColdStart", value=True)) == 1
    assert len(trace.get_metadata(key=handler_metadata_key, namespace=TracerStack.SERVICE_NAME)) == 2
    assert len(trace.get_subsegment(name=handler_subsegment)) == 2
