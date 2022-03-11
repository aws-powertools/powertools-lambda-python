import json

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

metrics = Metrics(namespace="ExampleApplication", service="booking")


def lambda_handler(evt, ctx):
    metrics.add_metric(name="ColdStart", unit=MetricUnit.Count, value=1)
    your_metrics_object = metrics.serialize_metric_set()
    metrics.clear_metrics()
    print(json.dumps(your_metrics_object))
