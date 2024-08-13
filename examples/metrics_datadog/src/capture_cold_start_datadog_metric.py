from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.metrics.provider.datadog import DatadogMetrics

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = DatadogMetrics()


@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext):
    return
