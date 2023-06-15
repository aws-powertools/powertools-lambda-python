from aws_lambda_powertools.metrics.provider.datadog_provider_draft import (
    DataDogMetrics,
    DataDogProvider,
)

dd_provider = DataDogProvider(namespace="default")
metrics = DataDogMetrics(provider=dd_provider)


@metrics.log_metrics(capture_cold_start_metric=True, raise_on_empty_metrics=False)
def lambda_handler(event, context):
    metrics.add_metric(name="item_sold", value=1, tags=["category:online"])
