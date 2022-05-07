import datetime
import json
import os
import uuid

import boto3
import pytest

from .. import utils

dirname = os.path.dirname(__file__)


@pytest.fixture(scope="module")
def config():
    return {"ANNOTATION_KEY": f"e2e-tracer-{uuid.uuid4()}", "ANNOTATION_VALUE": "stored"}


@pytest.fixture(scope="module")
def deploy_lambdas(deploy, config):
    handlers_dir = f"{dirname}/handlers/"

    lambda_arn = deploy(
        handlers_name=utils.find_handlers(handlers_dir),
        handlers_dir=handlers_dir,
        environment_variables=config,
    )
    start_date = datetime.datetime.utcnow()
    result = utils.trigger_lambda(lambda_arn=lambda_arn)
    assert result["Payload"].read() == b'"success"'
    return lambda_arn, start_date


@pytest.mark.e2e
def test_basic_lambda_trace_visible(deploy_lambdas, config):
    start_date = deploy_lambdas[1]
    end_date = start_date + datetime.timedelta(minutes=5)

    trace = utils.get_traces(
        start_date=start_date,
        end_date=end_date,
        lambda_function_name=deploy_lambdas[0].split(":")[-1],
        xray_client=boto3.client("xray"),
    )

    for segment in trace["Traces"][0]["Segments"]:
        document = json.loads(segment["Document"])
        if document["origin"] == "AWS::Lambda::Function":
            for subsegment in document["subsegments"]:
                if subsegment["name"] == "Invocation":
                    print(subsegment)
                    for x_subsegment in subsegment["subsegments"]:
                        metadata = x_subsegment["metadata"]
                        annotation = x_subsegment["annotations"]

    assert metadata["e2e-tests-app"][config["ANNOTATION_KEY"]] == config["ANNOTATION_VALUE"]
    assert annotation["Service"] == "e2e-tests-app"
