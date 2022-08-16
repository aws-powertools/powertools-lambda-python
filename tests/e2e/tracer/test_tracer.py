import json

import pytest
from e2e.utils import helpers


@pytest.fixture
def basic_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandlerArn", "")


@pytest.fixture
def basic_handler_fn(infrastructure: dict) -> str:
    return infrastructure.get("BasicHandler", "")


def test_basic_lambda_trace_is_visible(basic_handler_fn_arn: str, basic_handler_fn: str):
    # GIVEN
    service = helpers.build_service_name()
    annotations = helpers.build_put_annotations_input(sample=helpers.build_random_value())
    metadata = helpers.build_put_metadata_input(sample=helpers.build_random_value())
    trace_query = helpers.build_trace_default_query(function_name=basic_handler_fn, service_name=service)

    # WHEN
    event = json.dumps({"annotations": annotations, "metadata": metadata})
    _, execution_time = helpers.trigger_lambda(lambda_arn=basic_handler_fn_arn, payload=event)

    # THEN
    trace = helpers.get_traces(start_date=execution_time, filter_expression=trace_query)
    info = helpers.find_trace_additional_info(trace=trace)
    assert info is not None

    # # handler_trace_segment = [trace_segment for trace_segment in info if trace_segment.name == "## lambda_handler"][0]
    # # collect_payment_trace_segment = [
    # #     trace_segment for trace_segment in info if trace_segment.name == "## collect_payment"
    # # ][0]

    # # annotation_key = config["environment_variables"]["ANNOTATION_KEY"]
    # # expected_value = config["environment_variables"]["ANNOTATION_VALUE"]
    # # expected_async_value = config["environment_variables"]["ANNOTATION_ASYNC_VALUE"]

    # # assert handler_trace_segment.annotations["Service"] == "e2e-tests-app"
    # # assert handler_trace_segment.metadata["e2e-tests-app"][annotation_key] == expected_value
    # # assert collect_payment_trace_segment.metadata["e2e-tests-app"][annotation_key] == expected_async_value
