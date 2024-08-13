from __future__ import annotations

import os
from typing import TYPE_CHECKING

from aws_lambda_powertools import single_metric
from aws_lambda_powertools.metrics import MetricUnit

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

STAGE = os.getenv("STAGE", "dev")


def lambda_handler(event: dict, context: LambdaContext):
    with single_metric(name="MySingleMetric", unit=MetricUnit.Count, value=1) as metric:
        metric.add_dimension(name="environment", value=STAGE)
