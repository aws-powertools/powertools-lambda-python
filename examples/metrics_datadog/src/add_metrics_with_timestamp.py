from __future__ import annotations

import time
from typing import TYPE_CHECKING

from aws_lambda_powertools.metrics.provider.datadog import DatadogMetrics

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = DatadogMetrics()


@metrics.log_metrics  # ensures metrics are flushed upon request completion/failure
def lambda_handler(event: dict, context: LambdaContext):
    metrics.add_metric(name="SuccessfulBooking", value=1, timestamp=int(time.time()))
