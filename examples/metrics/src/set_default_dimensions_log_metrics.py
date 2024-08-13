from __future__ import annotations

import os
from typing import TYPE_CHECKING

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

STAGE = os.getenv("STAGE", "dev")
metrics = Metrics()
DEFAULT_DIMENSIONS = {"environment": STAGE, "another": "one"}


# ensures metrics are flushed upon request completion/failure
@metrics.log_metrics(default_dimensions=DEFAULT_DIMENSIONS)
def lambda_handler(event: dict, context: LambdaContext):
    metrics.add_metric(name="TurbineReads", unit=MetricUnit.Count, value=1)
    metrics.add_metric(name="TurbineReads", unit=MetricUnit.Count, value=8)
