import datetime
import json

import pytest

from tests.e2e.metrics.infrastructure import MetricsStack
from tests.e2e.utils import helpers

METRIC_NAMESPACE = "powertools-e2e-metric"


@pytest.fixture
def infra_outputs(infrastructure: MetricsStack):
    return infrastructure.get_stack_outputs()


@pytest.fixture
def basic_handler_fn(infra_outputs: dict) -> str:
    return infra_outputs.get("BasicHandlerArn", "")


def test_basic_lambda_metric_is_visible(basic_handler_fn):
    # GIVEN
    metric_name = helpers.build_metric_name()
    service = helpers.build_service_name()
    event = json.dumps({"metric_name": metric_name, "service": service, "namespace": METRIC_NAMESPACE})

    # WHEN
    ret, execution_time = helpers.trigger_lambda(lambda_arn=basic_handler_fn, payload=event)

    metrics = helpers.get_metrics(
        start_date=execution_time,
        end_date=execution_time + datetime.timedelta(minutes=2),
        namespace=METRIC_NAMESPACE,
        service_name=service,
        metric_name=metric_name,
    )

    # THEN
    assert len(metrics.get("Timestamps", [])) == 1
    metric_data = metrics.get("Values", [])
    assert metric_data and metric_data[0] == 1

    # for later... we could break the test early if the function failed
    # we could extend `trigger_lambda` with a default param to check on that
    # making the test less verbose. For explicit invoke failure, we could override
    assert ret is not None


# helpers: adjust retries and wait to be much smaller
# helpers: make retry config adjustable
# Infra: Add temporary Powertools Layer
# Powertools: should have a method to set namespace at runtime
# Create separate Infra class so they can live side by side
