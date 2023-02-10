from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricResolution, MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = Metrics()


@metrics.log_metrics  # ensures metrics are flushed upon request completion/failure
def lambda_handler(event: dict, context: LambdaContext):
    metrics.add_metric(name="SuccessfulBooking", unit=MetricUnit.Count, value=1, resolution=MetricResolution.High)
