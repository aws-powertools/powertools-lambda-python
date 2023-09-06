import pytest

from aws_lambda_powertools.metrics.exceptions import SchemaValidationError
from aws_lambda_powertools.metrics.provider.datadog import DatadogMetrics
from aws_lambda_powertools.metrics.provider.datadog.warnings import DatadogDataValidationWarning


def test_get_namespace_property(namespace):
    # GIVEN DatadogMetrics is initialized
    my_metrics = DatadogMetrics(namespace=namespace)

    # WHEN we try to access the namespace property
    # THEN namespace property must be present
    assert my_metrics.namespace == namespace


def test_set_namespace_property(namespace):
    # GIVEN DatadogMetrics is initialized
    my_metrics = DatadogMetrics()

    # WHEN we set the namespace property after ther initialization
    my_metrics.namespace = namespace

    # THEN namespace property must be present
    assert my_metrics.namespace == namespace


def test_default_tags_across_instances():
    # GIVEN DatadogMetrics is initialized and we persist a set of default tags
    my_metrics = DatadogMetrics()
    my_metrics.set_default_tags(environment="test", log_group="/lambda/test")

    # WHEN a new DatadogMetrics instance is created
    same_metrics = DatadogMetrics()

    # THEN default tags should also be present in the new instance
    assert "environment" in same_metrics.default_tags


def test_invalid_datadog_metric_name():
    metrics = DatadogMetrics()

    # GIVEN three metrics names with different invalid names
    metric_name_1 = "1_metric"  # Metric name must not start with number
    metric_name_2 = "metric_ç"  # Metric name must not contains unicode characters
    metric_name_3 = "".join(["x" for _ in range(201)])  # Metric name must have less than 200 characters

    # WHEN we try to validate those metrics names
    # THEN must be False
    with pytest.raises(SchemaValidationError, match="Invalid metric name.*"):
        metrics.add_metric(name=metric_name_1, value=1)

    with pytest.raises(SchemaValidationError, match="Invalid metric name.*"):
        metrics.add_metric(name=metric_name_2, value=1)

    with pytest.raises(SchemaValidationError, match="Invalid metric name.*"):
        metrics.add_metric(name=metric_name_3, value=1)


def test_invalid_datadog_metric_tag():
    metrics = DatadogMetrics()

    # GIVEN three metrics with different invalid tags
    metric_tag_1 = "".join(["x" for _ in range(201)])  # Metric tags must have less than 200 characters

    # WHEN we try to validate those metrics tags
    # THEN must be False
    with pytest.warns(DatadogDataValidationWarning):
        metrics.add_metric(name="metric_2", value=1, tag1=metric_tag_1)
