from aws_lambda_powertools.metrics import Metrics

metrics = Metrics()


@metrics.log_metrics(raise_on_empty_metrics=True)
def lambda_handler(evt, ctx):
    ...
