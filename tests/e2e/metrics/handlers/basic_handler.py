from aws_lambda_powertools import Metrics

my_metrics = Metrics()


@my_metrics.log_metrics
def lambda_handler(event, context):
    metrics, namespace, service = event.get("metrics"), event.get("namespace"), event.get("service")

    # Maintenance: create a public method to set these explicitly
    my_metrics.namespace = namespace
    my_metrics.service = service

    for metric in metrics:
        my_metrics.add_metric(**metric)

    return "success"
