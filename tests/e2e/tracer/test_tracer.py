import datetime
import uuid

import boto3
import pytest
from e2e import conftest
from e2e.utils import helpers


@pytest.fixture(scope="module")
def config() -> conftest.LambdaConfig:
    return {
        "parameters": {"tracing": "ACTIVE"},
        "environment_variables": {
            "ANNOTATION_KEY": f"e2e-tracer-{str(uuid.uuid4()).replace('-','_')}",
            "ANNOTATION_VALUE": "stored",
            "ANNOTATION_ASYNC_VALUE": "payments",
        },
    }


def test_basic_lambda_async_trace_visible(execute_lambda: conftest.InfrastructureOutput, config: conftest.LambdaConfig):
    # GIVEN
    lambda_name = execute_lambda.get_lambda_function_name(cf_output_name="basichandlerarn")
    start_date = execute_lambda.get_lambda_execution_time()
    end_date = start_date + datetime.timedelta(minutes=5)
    trace_filter_exporession = f'service("{lambda_name}")'

    # WHEN
    trace = helpers.get_traces(
        start_date=start_date,
        end_date=end_date,
        filter_expression=trace_filter_exporession,
        xray_client=boto3.client("xray"),
    )

    # THEN
    info = helpers.find_trace_additional_info(trace=trace)
    print(info)
    handler_trace_segment = [trace_segment for trace_segment in info if trace_segment.name == "## lambda_handler"][0]
    collect_payment_trace_segment = [
        trace_segment for trace_segment in info if trace_segment.name == "## collect_payment"
    ][0]

    annotation_key = config["environment_variables"]["ANNOTATION_KEY"]
    expected_value = config["environment_variables"]["ANNOTATION_VALUE"]
    expected_async_value = config["environment_variables"]["ANNOTATION_ASYNC_VALUE"]

    assert handler_trace_segment.annotations["Service"] == "e2e-tests-app"
    assert handler_trace_segment.metadata["e2e-tests-app"][annotation_key] == expected_value
    assert collect_payment_trace_segment.metadata["e2e-tests-app"][annotation_key] == expected_async_value
