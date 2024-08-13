from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools import Metrics

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = Metrics()


@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext): ...
