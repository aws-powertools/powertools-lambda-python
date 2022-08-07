import datetime
import json
import uuid
from typing import Dict, Type

import pytest
from e2e import conftest
from e2e.utils import helpers

from tests.e2e.metrics.infrastructure import MetricsStack


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


@pytest.fixture
def infra_outputs(infrastructure: Type[MetricsStack]):
    return infrastructure.get_stack_outputs()


def test_basic_lambda_metric_is_visible(infra_outputs: Dict[str, str]):
    # sourcery skip: aware-datetime-for-utc
    execution_time = datetime.datetime.utcnow()
    metric_name = "test"
    service = "test-metric-is-visible"
    namespace = "powertools-e2e-metric"
    event = json.dumps({"metric_name": metric_name, "service": service, "namespace": namespace})
    ret = helpers.trigger_lambda(lambda_arn=infra_outputs.get("basichandlerarn"), payload=event)

    assert ret is None  # we could test in the actual response now

    # NOTE: find out why we're getting empty metrics
    metrics = helpers.get_metrics(
        start_date=execution_time,
        end_date=execution_time + datetime.timedelta(minutes=2),
        namespace=namespace,
        service_name=service,
        metric_name=metric_name,
    )
    assert metrics is not None


# helpers: create client on the fly if not passed
#          accept payload to be sent as part of invocation
# helpers: adjust retries and wait to be much smaller
# Infra: Create dynamic Enum/DataClass to reduce guessing on outputs
# Infra: Fix outputs
# Infra: Add temporary Powertools Layer
# Powertools: should have a method to set namespace at runtime
