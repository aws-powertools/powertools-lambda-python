from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

metrics = Metrics(namespace="ExampleApplication", service="ExampleService")


@metrics.log_metrics
def lambda_handler(evt, ctx):
    metrics.add_metric(name="BookingConfirmation", unit=MetricUnit.Count, value=1)
