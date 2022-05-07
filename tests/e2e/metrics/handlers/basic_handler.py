import os

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

METRIC_NAMESPACE = os.environ["METRIC_NAMESPACE"]
METRIC_NAME = os.environ["METRIC_NAME"]
SERVICE_NAME = os.environ["SERVICE_NAME"]

metrics = Metrics(namespace=METRIC_NAMESPACE, service=SERVICE_NAME)


@metrics.log_metrics
def lambda_handler(event, context):
    metrics.add_metric(name=METRIC_NAME, unit=MetricUnit.Count, value=1)
    return "success"
