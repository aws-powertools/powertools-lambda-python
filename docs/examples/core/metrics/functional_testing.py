import json

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit


def test_log_metrics(capsys):
    # GIVEN Metrics is initialized
    metrics = Metrics(namespace="ServerlessAirline")

    # WHEN we utilize log_metrics to serialize
    # and flush all metrics at the end of a function execution
    @metrics.log_metrics
    def lambda_handler(evt, ctx):
        metrics.add_metric(name="SuccessfulBooking", unit=MetricUnit.Count, value=1)
        metrics.add_dimension(name="environment", value="prod")

    lambda_handler({}, {})
    log = capsys.readouterr().out.strip()  # remove any extra line
    metrics_output = json.loads(log)  # deserialize JSON str

    # THEN we should have no exceptions
    # and a valid EMF object should be flushed correctly
    assert "SuccessfulBooking" in log  # basic string assertion in JSON str
    assert "SuccessfulBooking" in metrics_output["_aws"]["CloudWatchMetrics"][0]["Metrics"][0]["Name"]
