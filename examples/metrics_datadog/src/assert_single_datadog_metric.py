import add_datadog_metrics


def test_log_metrics(capsys):
    add_datadog_metrics.lambda_handler({}, {})

    log = capsys.readouterr().out.strip()  # remove any extra line

    assert "SuccessfulBooking" in log  # basic string assertion in JSON str
