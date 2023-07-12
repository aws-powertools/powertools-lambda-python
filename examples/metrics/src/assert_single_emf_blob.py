import json

import add_metrics


def test_log_metrics(capsys):
    add_metrics.lambda_handler({}, {})

    log = capsys.readouterr().out.strip()  # remove any extra line
    metrics_output = json.loads(log)  # deserialize JSON str

    # THEN we should have no exceptions
    # and a valid EMF object should be flushed correctly
    assert "SuccessfulBooking" in log  # basic string assertion in JSON str
    assert "SuccessfulBooking" in metrics_output["_aws"]["CloudWatchMetrics"][0]["Metrics"][0]["Name"]
