import datetime
import json
import uuid

import boto3
import pytest

from .. import conftest
from ..utils import helpers


@pytest.fixture(scope="module")
def config():
    return {
        "parameters": {"tracing": "ACTIVE"},
        "environment_variables": {"ANNOTATION_KEY": f"e2e-tracer-{uuid.uuid4()}", "ANNOTATION_VALUE": "stored"},
    }


@pytest.mark.e2e
def test_basic_lambda_trace_visible(execute_lambda: conftest.InfrastructureOutput, config: conftest.LambdaConfig):
    lambda_arn = execute_lambda.get_lambda_arn(name="basichandlerarn")
    start_date = execute_lambda.get_lambda_execution_time()
    end_date = start_date + datetime.timedelta(minutes=5)

    trace = helpers.get_traces(
        start_date=start_date,
        end_date=end_date,
        lambda_function_name=lambda_arn.split(":")[-1],
        xray_client=boto3.client("xray"),
    )

    for segment in trace["Traces"][0]["Segments"]:
        document = json.loads(segment["Document"])
        if document["origin"] == "AWS::Lambda::Function":
            for subsegment in document["subsegments"]:
                if subsegment["name"] == "Invocation":
                    for x_subsegment in subsegment["subsegments"]:
                        metadata = x_subsegment["metadata"]
                        annotation = x_subsegment["annotations"]

    assert (
        metadata["e2e-tests-app"][config["environment_variables"]["ANNOTATION_KEY"]]
        == config["environment_variables"]["ANNOTATION_VALUE"]
    )
    assert annotation["Service"] == "e2e-tests-app"
