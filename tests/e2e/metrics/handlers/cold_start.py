from aws_lambda_powertools import Metrics

my_metrics = Metrics()


@my_metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    # Maintenance: create a public method to set these explicitly
    my_metrics.namespace = event.get("namespace")
    my_metrics.service = event.get("service")

    return "success"
