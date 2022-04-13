import json
from collections import namedtuple

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit


def capture_metrics_output_multiple_emf_objects(capsys):
    return [json.loads(line.strip()) for line in capsys.readouterr().out.split("\n") if line]


def test_log_metrics(capsys):
    # GIVEN Metrics is initialized
    metrics = Metrics(namespace="ServerlessAirline")

    # WHEN log_metrics is used with capture_cold_start_metric
    @metrics.log_metrics(capture_cold_start_metric=True)
    def lambda_handler(evt, ctx):
        metrics.add_metric(name="SuccessfulBooking", unit=MetricUnit.Count, value=1)
        metrics.add_dimension(name="environment", value="prod")

    # log_metrics uses function_name property from context to add as a dimension for cold start metric
    LambdaContext = namedtuple("LambdaContext", "function_name")
    lambda_handler({}, LambdaContext("example_fn"))

    cold_start_blob, custom_metrics_blob = capture_metrics_output_multiple_emf_objects(capsys)

    # THEN ColdStart metric and function_name dimension should be logged
    # in a separate EMF blob than the application metrics
    assert cold_start_blob["ColdStart"] == [1.0]
    assert cold_start_blob["function_name"] == "example_fn"

    assert "SuccessfulBooking" in custom_metrics_blob  # as per previous example
