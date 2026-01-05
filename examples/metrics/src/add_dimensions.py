from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = Metrics()


@metrics.log_metrics
def lambda_handler(event: dict, context: LambdaContext):
    # Add primary dimension
    metrics.add_dimension(name="service", value="booking")

    # Add multiple dimension sets for different aggregation views
    metrics.add_dimensions(environment="prod", region="us-east-1")
    metrics.add_dimensions(environment="prod")

    metrics.add_metric(name="SuccessfulBooking", unit=MetricUnit.Count, value=1)
