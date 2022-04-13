from aws_lambda_powertools import Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit

tracer = Tracer(service="booking")
metrics = Metrics(namespace="ExampleApplication", service="booking")


@metrics.log_metrics
@tracer.capture_lambda_handler
def lambda_handler(evt, ctx):
    metrics.add_metric(name="BookingConfirmation", unit=MetricUnit.Count, value=1)
