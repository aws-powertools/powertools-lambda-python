import add_metrics_without_provider


def test_log_metrics(capsys):
    add_metrics_without_provider.lambda_handler({}, {})

    log = capsys.readouterr().out.strip()  # remove any extra line

    assert "SuccessfulBooking" in log  # basic string assertion in JSON str
