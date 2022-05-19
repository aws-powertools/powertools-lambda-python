import datetime
import uuid

import boto3
import pytest

from ..utils import helpers


@pytest.fixture(scope="module")
def config():
    return {
        "parameters": {},
        "environment_variables": {
            "METRIC_NAMESPACE": f"powertools-e2e-metric-{uuid.uuid4()}",
            "METRIC_NAME": "business-metric",
            "SERVICE_NAME": "test-powertools-service",
        },
    }


@pytest.mark.e2e
def test_basic_lambda_metric_visible(execute_lambda, config):
    start_date = execute_lambda["execution_time"]
    end_date = start_date + datetime.timedelta(minutes=5)

    metrics = helpers.get_metrics(
        start_date=start_date,
        end_date=end_date,
        namespace=config["environment_variables"]["METRIC_NAMESPACE"],
        metric_name=config["environment_variables"]["METRIC_NAME"],
        service_name=config["environment_variables"]["SERVICE_NAME"],
        cw_client=boto3.client(service_name="cloudwatch"),
    )
    assert metrics["Timestamps"] and len(metrics["Timestamps"]) == 1
    assert metrics["Values"] and len(metrics["Values"]) == 1
    assert metrics["Values"][0] == 1
