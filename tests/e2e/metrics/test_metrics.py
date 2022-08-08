import datetime
import json
from typing import Dict, Type

import pytest
from e2e.utils import helpers

from tests.e2e.metrics.infrastructure import MetricsStack


@pytest.fixture
def infra_outputs(infrastructure: Type[MetricsStack]):
    return infrastructure.get_stack_outputs()


def test_basic_lambda_metric_is_visible(infra_outputs: Dict[str, str]):
    # GIVEN
    metric_name = "test-two"
    service = "test-metric-is-visible"
    namespace = "powertools-e2e-metric"
    event = json.dumps({"metric_name": metric_name, "service": service, "namespace": namespace})

    # NOTE: Need to try creating a dynamic enum/dataclass w/ Literal types to make discovery easier
    # it might not be possible

    # WHEN
    execution_time = datetime.datetime.utcnow()
    ret = helpers.trigger_lambda(lambda_arn=infra_outputs.get("basichandlerarn"), payload=event)

    metrics = helpers.get_metrics(
        start_date=execution_time,
        end_date=execution_time + datetime.timedelta(minutes=2),
        namespace=namespace,
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
# Infra: Create dynamic Enum/DataClass to reduce guessing on outputs
# Infra: Fix outputs
# Infra: Add temporary Powertools Layer
# Powertools: should have a method to set namespace at runtime
# Create separate Infra class so they can live side by side
