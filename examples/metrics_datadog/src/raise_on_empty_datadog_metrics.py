from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.metrics.provider.datadog import DatadogMetrics

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = DatadogMetrics()


@metrics.log_metrics(raise_on_empty_metrics=True)  # ensures metrics are flushed upon request completion/failure
def lambda_handler(event: dict, context: LambdaContext):
    # no metrics being created will now raise SchemaValidationError
    return
