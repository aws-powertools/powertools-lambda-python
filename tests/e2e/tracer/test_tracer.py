import pytest

from tests.e2e.tracer.handlers import async_capture, basic_handler
from tests.e2e.tracer.infrastructure import TracerStack
from tests.e2e.utils import data_builder, data_fetcher


@pytest.fixture
def basic_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandlerArn", "")


@pytest.fixture
def basic_handler_fn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandler", "")


@pytest.fixture
def same_function_name_fn(infrastructure: dict) -> str:
    return infrastructure.get("SameFunctionName", "")


@pytest.fixture
def same_function_name_arn(infrastructure: dict) -> str:
    return infrastructure.get("SameFunctionNameArn", "")


@pytest.fixture
def async_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("AsyncCaptureArn", "")


@pytest.fixture
def async_fn(infrastructure: dict) -> str:
    return infrastructure.get("AsyncCapture", "")


def test_lambda_handler_trace_is_visible(basic_handler_fn_arn: str, basic_handler_fn: str):
    # GIVEN
    handler_name = basic_handler.lambda_handler.__name__
    handler_subsegment = f"## {handler_name}"
    handler_metadata_key = f"{handler_name} response"

    method_name = f"basic_handler.{basic_handler.get_todos.__name__}"
    method_subsegment = f"## {method_name}"
    method_metadata_key = f"{method_name} response"

    trace_query = data_builder.build_trace_default_query(function_name=basic_handler_fn)

    # WHEN
    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn)
    data_fetcher.get_lambda_response(lambda_arn=basic_handler_fn_arn)

    # THEN
    trace = data_fetcher.get_traces(start_date=execution_time, filter_expression=trace_query, minimum_traces=2)

    assert len(trace.get_annotation(key="ColdStart", value=True)) == 1
    assert len(trace.get_metadata(key=handler_metadata_key, namespace=TracerStack.SERVICE_NAME)) == 2
    assert len(trace.get_metadata(key=method_metadata_key, namespace=TracerStack.SERVICE_NAME)) == 2
    assert len(trace.get_subsegment(name=handler_subsegment)) == 2
    assert len(trace.get_subsegment(name=method_subsegment)) == 2


def test_lambda_handler_trace_multiple_functions_same_name(same_function_name_arn: str, same_function_name_fn: str):
    # GIVEN
    method_name_1 = "same_function_name.Todos.get_all"
    method_subsegment_1 = f"## {method_name_1}"
    method_metadata_key_1 = f"{method_name_1} response"

    method_name_2 = "same_function_name.Comments.get_all"
    method_subsegment_2 = f"## {method_name_2}"
    method_metadata_key_2 = f"{method_name_2} response"

    trace_query = data_builder.build_trace_default_query(function_name=same_function_name_fn)

    # WHEN
    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=same_function_name_arn)
    data_fetcher.get_lambda_response(lambda_arn=same_function_name_arn)

    # THEN
    trace = data_fetcher.get_traces(start_date=execution_time, filter_expression=trace_query)

    assert len(trace.get_metadata(key=method_metadata_key_1, namespace=TracerStack.SERVICE_NAME)) == 1
    assert len(trace.get_metadata(key=method_metadata_key_2, namespace=TracerStack.SERVICE_NAME)) == 1
    assert len(trace.get_subsegment(name=method_subsegment_1)) == 1
    assert len(trace.get_subsegment(name=method_subsegment_2)) == 1


def test_async_trace_is_visible(async_fn_arn: str, async_fn: str):
    # GIVEN
    async_fn_name = f"async_capture.{async_capture.async_get_users.__name__}"
    async_fn_name_subsegment = f"## {async_fn_name}"
    async_fn_name_metadata_key = f"{async_fn_name} response"

    trace_query = data_builder.build_trace_default_query(function_name=async_fn)

    # WHEN
    _, execution_time = data_fetcher.get_lambda_response(lambda_arn=async_fn_arn)

    # THEN
    trace = data_fetcher.get_traces(start_date=execution_time, filter_expression=trace_query)

    assert len(trace.get_subsegment(name=async_fn_name_subsegment)) == 1
    assert len(trace.get_metadata(key=async_fn_name_metadata_key, namespace=TracerStack.SERVICE_NAME)) == 1
