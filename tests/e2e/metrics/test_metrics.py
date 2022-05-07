import datetime
import os
import uuid

import boto3
import pytest

from .. import utils

dirname = os.path.dirname(__file__)


@pytest.fixture(scope="module")
def config():
    return {
        "METRIC_NAMESPACE": f"powertools-e2e-metric-{uuid.uuid4()}",
        "METRIC_NAME": "business-metric",
        "SERVICE_NAME": "test-powertools-service",
    }


@pytest.fixture(scope="module")
def deploy_basic_lambda(deploy_infrastructure, config):
    lambda_arn = deploy_infrastructure(
        handler_filename=f"{dirname}/handlers/basic_handler.py",
        environment_variables=config,
    )
    start_date = datetime.datetime.now(datetime.timezone.utc)
    result = utils.trigger_lambda(lambda_arn=lambda_arn)
    assert result["Payload"].read() == b'"success"'
    return start_date


@pytest.mark.e2e
def test_basic_lambda_metric_visible(deploy_basic_lambda, config):
    start_date = deploy_basic_lambda
    end_date = start_date + datetime.timedelta(minutes=5)

    metrics = utils.get_metrics(
        start_date=start_date,
        end_date=end_date,
        namespace=config["METRIC_NAMESPACE"],
        metric_name=config["METRIC_NAME"],
        service_name=config["SERVICE_NAME"],
        cw_client=boto3.client(service_name="cloudwatch"),
    )
    assert metrics["Timestamps"] and len(metrics["Timestamps"]) == 1
    assert metrics["Values"] and len(metrics["Values"]) == 1
    assert metrics["Values"][0] == 1
