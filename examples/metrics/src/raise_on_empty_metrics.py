from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.metrics import Metrics

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = Metrics()


@metrics.log_metrics(raise_on_empty_metrics=True)
def lambda_handler(event: dict, context: LambdaContext):
    # no metrics being created will now raise SchemaValidationError
    ...
