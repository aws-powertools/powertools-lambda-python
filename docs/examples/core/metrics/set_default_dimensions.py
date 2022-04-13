from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

metrics = Metrics(namespace="ExampleApplication", service="booking")
metrics.set_default_dimensions(environment="prod", another="one")


@metrics.log_metrics
def lambda_handler(evt, ctx):
    metrics.add_metric(name="SuccessfulBooking", unit=MetricUnit.Count, value=1)
