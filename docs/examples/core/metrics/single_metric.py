from aws_lambda_powertools import single_metric
from aws_lambda_powertools.metrics import MetricUnit


def lambda_handler(evt, ctx):
    with single_metric(name="ColdStart", unit=MetricUnit.Count, value=1, namespace="ExampleApplication") as metric:
        metric.add_dimension(name="function_context", value="$LATEST")
        ...
