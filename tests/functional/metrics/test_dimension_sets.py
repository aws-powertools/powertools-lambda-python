"""
Tests for multiple dimension sets feature
"""

from __future__ import annotations

import json

import pytest

from aws_lambda_powertools.metrics import Metrics, MetricUnit, SchemaValidationError
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.cloudwatch import AmazonCloudWatchEMFProvider


def test_add_dimensions_creates_multiple_dimension_sets(capsys):
    # GIVEN a metrics instance
    metrics = AmazonCloudWatchEMFProvider(namespace="TestApp")

    # WHEN we add multiple dimension sets
    metrics.add_dimension(name="service", value="booking")
    metrics.add_dimensions(environment="prod", region="us-east-1")
    metrics.add_dimensions(environment="prod")
    metrics.add_dimensions(region="us-east-1")
    metrics.add_metric(name="SuccessfulRequests", unit=MetricUnit.Count, value=10)

    # THEN the serialized output should contain multiple dimension arrays
    output = metrics.serialize_metric_set()

    assert len(output["_aws"]["CloudWatchMetrics"]) == 1
    dimensions = output["_aws"]["CloudWatchMetrics"][0]["Dimensions"]

    # Should have 4 dimension sets: primary + 3 added
    assert len(dimensions) == 4
    assert dimensions[0] == ["service"]  # Primary dimension set
    assert set(dimensions[1]) == {"environment", "region"}
    assert dimensions[2] == ["environment"]
    assert dimensions[3] == ["region"]

    # All dimension values should be in the root
    assert output["service"] == "booking"
    assert output["environment"] == "prod"
    assert output["region"] == "us-east-1"
    assert output["SuccessfulRequests"] == [10.0]


def test_add_dimensions_with_metrics_wrapper(capsys):
    # GIVEN a Metrics instance (not provider directly)
    metrics = Metrics(namespace="TestApp", service="payment")

    # WHEN we use add_dimensions through the Metrics wrapper
    @metrics.log_metrics
    def handler(event, context):
        metrics.add_dimensions(environment="staging", region="us-west-2")
        metrics.add_dimensions(environment="staging")
        metrics.add_metric(name="PaymentProcessed", unit=MetricUnit.Count, value=1)

    handler({}, {})

    # THEN the output should contain multiple dimension sets
    output = json.loads(capsys.readouterr().out.strip())

    dimensions = output["_aws"]["CloudWatchMetrics"][0]["Dimensions"]
    assert len(dimensions) == 3  # Primary (service) + 2 added

    # Primary dimension from service parameter
    assert "service" in dimensions[0]

    # Check added dimension sets - they don't include service unless it's a default dimension
    assert set(dimensions[1]) == {"environment", "region"}
    assert set(dimensions[2]) == {"environment"}


def test_add_dimensions_with_default_dimensions():
    # GIVEN metrics with default dimensions
    metrics = AmazonCloudWatchEMFProvider(namespace="TestApp")
    metrics.set_default_dimensions(tenant_id="123", application="api")

    # WHEN we add dimension sets after setting defaults
    metrics.add_dimensions(environment="prod")
    metrics.add_dimensions(region="eu-west-1")
    metrics.add_metric(name="ApiCalls", unit=MetricUnit.Count, value=5)

    # THEN default dimensions should be included in all dimension sets
    output = metrics.serialize_metric_set()
    dimensions = output["_aws"]["CloudWatchMetrics"][0]["Dimensions"]

    # Each dimension set should include default dimensions
    assert set(dimensions[1]) == {"tenant_id", "application", "environment"}
    assert set(dimensions[2]) == {"tenant_id", "application", "region"}

    # Values should be in root
    assert output["tenant_id"] == "123"
    assert output["application"] == "api"
    assert output["environment"] == "prod"
    assert output["region"] == "eu-west-1"


def test_add_dimensions_duplicate_keys_last_value_wins():
    # GIVEN metrics with overlapping dimension keys
    metrics = AmazonCloudWatchEMFProvider(namespace="TestApp")

    # WHEN we add dimension sets with duplicate keys
    metrics.add_dimensions(environment="dev", region="us-east-1")
    metrics.add_dimensions(environment="staging", region="us-west-2")
    metrics.add_dimensions(environment="prod")  # Last value for environment
    metrics.add_metric(name="TestMetric", unit=MetricUnit.Count, value=1)

    # THEN the last value should be used in the root
    output = metrics.serialize_metric_set()

    # Last values should win
    assert output["environment"] == "prod"
    assert output["region"] == "us-west-2"


def test_add_dimensions_empty_kwargs_warns():
    # GIVEN metrics instance
    metrics = AmazonCloudWatchEMFProvider(namespace="TestApp")

    # WHEN we call add_dimensions without arguments
    with pytest.warns(UserWarning, match="Empty dimensions dictionary"):
        metrics.add_dimensions()

    # THEN no dimension set should be added
    assert len(metrics.dimension_sets) == 0


def test_add_dimensions_invalid_dimensions_skipped():
    # GIVEN metrics instance
    metrics = AmazonCloudWatchEMFProvider(namespace="TestApp")

    # WHEN we add dimensions with empty values
    with pytest.warns(UserWarning, match="empty name or value"):
        metrics.add_dimensions(key="")

    # THEN no dimension set should be added
    assert len(metrics.dimension_sets) == 0


def test_add_dimensions_exceeds_max_dimensions():
    # GIVEN metrics with many dimensions
    metrics = AmazonCloudWatchEMFProvider(namespace="TestApp")

    # Add 29 dimensions to primary set (max is 30)
    for i in range(29):
        metrics.add_dimension(name=f"dim{i}", value=f"val{i}")

    # WHEN we try to add dimension set that would exceed max
    # THEN it should raise SchemaValidationError
    with pytest.raises(SchemaValidationError, match="Maximum dimensions"):
        metrics.add_dimensions(extra1="val1", extra2="val2")


def test_add_dimensions_converts_values_to_strings():
    # GIVEN metrics instance
    metrics = AmazonCloudWatchEMFProvider(namespace="TestApp")

    # WHEN we add dimensions with non-string values (using **dict for non-string values)
    metrics.add_dimensions(**{"count": 123, "is_active": True, "ratio": 3.14})
    metrics.add_metric(name="TestMetric", unit=MetricUnit.Count, value=1)

    # THEN values should be converted to strings
    output = metrics.serialize_metric_set()
    assert output["count"] == "123"
    assert output["is_active"] == "True"
    assert output["ratio"] == "3.14"


def test_clear_metrics_clears_dimension_sets(capsys):
    # GIVEN metrics with dimension sets
    metrics = Metrics(namespace="TestApp", service="api")

    @metrics.log_metrics
    def handler(event, context):
        metrics.add_dimensions(environment="prod")
        metrics.add_dimensions(region="us-east-1")
        metrics.add_metric(name="Requests", unit=MetricUnit.Count, value=1)

    handler({}, {})

    # WHEN we call clear_metrics (done automatically by decorator)
    # THEN dimension_sets should be cleared
    assert len(metrics.provider.dimension_sets) == 0


def test_add_dimensions_order_preserved():
    # GIVEN metrics instance
    metrics = AmazonCloudWatchEMFProvider(namespace="TestApp")

    # WHEN we add dimension sets in specific order
    metrics.add_dimension(name="service", value="api")
    metrics.add_dimensions(environment="prod", region="us-east-1")
    metrics.add_dimensions(environment="prod")
    metrics.add_dimensions(region="us-east-1")
    metrics.add_metric(name="TestMetric", unit=MetricUnit.Count, value=1)

    # THEN dimension sets should appear in order added
    output = metrics.serialize_metric_set()
    dimensions = output["_aws"]["CloudWatchMetrics"][0]["Dimensions"]

    assert dimensions[0] == ["service"]
    assert set(dimensions[1]) == {"environment", "region"}
    assert dimensions[2] == ["environment"]
    assert dimensions[3] == ["region"]


def test_add_dimensions_with_metadata():
    # GIVEN metrics with metadata
    metrics = AmazonCloudWatchEMFProvider(namespace="TestApp")

    # WHEN we add dimension sets and metadata
    metrics.add_dimensions(environment="prod")
    metrics.add_metadata(key="request_id", value="abc-123")
    metrics.add_metric(name="ApiLatency", unit=MetricUnit.Milliseconds, value=150)

    # THEN both should be in output
    output = metrics.serialize_metric_set()

    assert "environment" in output
    assert output["request_id"] == "abc-123"
    # Primary dimension_set + 1 additional dimension set
    assert len(output["_aws"]["CloudWatchMetrics"][0]["Dimensions"]) == 2


def test_multiple_metrics_with_dimension_sets():
    # GIVEN metrics with multiple metrics and dimension sets
    metrics = AmazonCloudWatchEMFProvider(namespace="TestApp")

    # WHEN we add multiple metrics with dimension sets
    metrics.add_dimensions(environment="prod", region="us-east-1")
    metrics.add_dimensions(environment="prod")
    metrics.add_metric(name="SuccessCount", unit=MetricUnit.Count, value=100)
    metrics.add_metric(name="ErrorCount", unit=MetricUnit.Count, value=5)
    metrics.add_metric(name="Latency", unit=MetricUnit.Milliseconds, value=250)

    # THEN all metrics should share the same dimension sets
    output = metrics.serialize_metric_set()

    assert len(output["_aws"]["CloudWatchMetrics"][0]["Metrics"]) == 3
    # Primary (empty) + 2 added dimension sets
    assert len(output["_aws"]["CloudWatchMetrics"][0]["Dimensions"]) == 3
    assert output["SuccessCount"] == [100.0]
    assert output["ErrorCount"] == [5.0]
    assert output["Latency"] == [250.0]


def test_add_dimensions_with_high_resolution_metrics():
    # GIVEN metrics with high resolution
    metrics = AmazonCloudWatchEMFProvider(namespace="TestApp")

    # WHEN we add dimension sets with high-resolution metrics
    metrics.add_dimensions(function="process_order")
    metrics.add_metric(
        name="ProcessingTime",
        unit=MetricUnit.Milliseconds,
        value=45,
        resolution=1,  # High resolution
    )

    # THEN dimension sets should work with high-resolution metrics
    output = metrics.serialize_metric_set()

    # Primary (empty) + 1 added dimension set
    assert len(output["_aws"]["CloudWatchMetrics"][0]["Dimensions"]) == 2
    assert output["_aws"]["CloudWatchMetrics"][0]["Metrics"][0]["StorageResolution"] == 1
