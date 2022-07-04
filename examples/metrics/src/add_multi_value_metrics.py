import os

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

STAGE = os.getenv("STAGE", "dev")
metrics = Metrics()


@metrics.log_metrics  # ensures metrics are flushed upon request completion/failure
def lambda_handler(event: dict, context: LambdaContext):
    metrics.add_dimension(name="environment", value=STAGE)
    metrics.add_metric(name="TurbineReads", unit=MetricUnit.Count, value=1)
    metrics.add_metric(name="TurbineReads", unit=MetricUnit.Count, value=8)
