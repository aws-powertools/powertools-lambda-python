from aws_lambda_powertools.metrics import EphemeralMetrics, MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = EphemeralMetrics()


@metrics.log_metrics
def lambda_handler(event: dict, context: LambdaContext):
    metrics.add_metric(name="SuccessfulBooking", unit=MetricUnit.Count, value=1)
