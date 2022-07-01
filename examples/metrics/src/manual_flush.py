import json

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = Metrics()


def lambda_handler(event: dict, context: LambdaContext):
    metrics.add_metric(name="SuccessfulBooking", unit=MetricUnit.Count, value=1)
    your_metrics_object = metrics.serialize_metric_set()
    metrics.clear_metrics()
    print(json.dumps(your_metrics_object))
