from aws_lambda_powertools import Metrics

metrics = Metrics(service="ExampleService")


@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(evt, ctx):
    ...
