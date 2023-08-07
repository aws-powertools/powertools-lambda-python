from aws_lambda_powertools.metrics.provider import (
    MetricsProviderBase,
)
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.cloudwatch import AmazonCloudWatchEMFProvider


def test_amazoncloudwatchemf_is_subclass_of_metricsproviderbase():
    assert issubclass(AmazonCloudWatchEMFProvider, MetricsProviderBase)
