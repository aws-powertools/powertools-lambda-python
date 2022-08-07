from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

metrics = Metrics()


@metrics.log_metrics
def lambda_handler(event, context):
    metric = event.get("metric_name")
    metrics.namespace = "powertools-e2e-metric"
    metrics.service = event.get("service")

    metrics.add_metric(name=metric, unit=MetricUnit.Count, value=1)
    return "success"
