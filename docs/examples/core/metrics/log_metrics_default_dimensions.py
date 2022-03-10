from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

metrics = Metrics(namespace="ExampleApplication", service="booking")
DEFAULT_DIMENSIONS = {"environment": "prod", "another": "one"}


@metrics.log_metrics(default_dimensions=DEFAULT_DIMENSIONS)
def lambda_handler(evt, ctx):
    metrics.add_metric(name="SuccessfulBooking", unit=MetricUnit.Count, value=1)
