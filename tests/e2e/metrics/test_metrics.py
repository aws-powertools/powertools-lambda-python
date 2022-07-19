import datetime
import uuid

import boto3
import pytest
from e2e import conftest
from e2e.utils import helpers


@pytest.fixture(scope="module")
def config() -> conftest.LambdaConfig:
    return {
        "parameters": {},
        "environment_variables": {
            "POWERTOOLS_METRICS_NAMESPACE": "powertools-e2e-metric",
            "POWERTOOLS_SERVICE_NAME": "test-powertools-service",
            "METRIC_NAME": f"business-metric-{str(uuid.uuid4()).replace('-','_')}",
        },
    }


def test_basic_lambda_metric_visible(execute_lambda: conftest.InfrastructureOutput, config: conftest.LambdaConfig):
    # GIVEN
    start_date = execute_lambda.get_lambda_execution_time()
    end_date = start_date + datetime.timedelta(minutes=5)

    # WHEN
    metrics = helpers.get_metrics(
        start_date=start_date,
        end_date=end_date,
        namespace=config["environment_variables"]["POWERTOOLS_METRICS_NAMESPACE"],
        metric_name=config["environment_variables"]["METRIC_NAME"],
        service_name=config["environment_variables"]["POWERTOOLS_SERVICE_NAME"],
        cw_client=boto3.client(service_name="cloudwatch"),
    )

    # THEN
    assert metrics.get("Timestamps") and len(metrics.get("Timestamps")) == 1
    assert metrics.get("Values") and len(metrics.get("Values")) == 1
    assert metrics.get("Values") and metrics.get("Values")[0] == 1
