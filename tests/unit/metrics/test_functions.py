import pytest

from aws_lambda_powertools.metrics.functions import (
    extract_cloudwatch_metric_resolution_value,
    extract_cloudwatch_metric_unit_value,
    serialize_datadog_tags,
    validate_datadog_metric_name,
)
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.exceptions import (
    MetricResolutionError,
    MetricUnitError,
)
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.metric_properties import MetricResolution, MetricUnit


def test_extract_invalid_cloudwatch_metric_resolution_value():
    metric_resolutions = [resolution.value for resolution in MetricResolution]

    # GIVEN an invalid EMF resolution value
    resolution = 2

    # WHEN try to extract this value
    # THEN must fail with MetricResolutionError
    with pytest.raises(MetricResolutionError, match="Invalid metric resolution.*"):
        extract_cloudwatch_metric_resolution_value(metric_resolutions, resolution=resolution)


def test_extract_valid_cloudwatch_metric_resolution_value():
    metric_resolutions = [resolution.value for resolution in MetricResolution]

    # GIVEN a valid EMF resolution value
    resolution = 1

    # WHEN try to extract this value
    extracted_resolution_value = extract_cloudwatch_metric_resolution_value(metric_resolutions, resolution=resolution)

    # THEN value must be extracted
    assert extracted_resolution_value == resolution


def test_extract_invalid_cloudwatch_metric_unit_value():
    metric_units = [unit.value for unit in MetricUnit]
    metric_unit_valid_options = list(MetricUnit.__members__)

    # GIVEN an invalid EMF unit value
    unit = "Fake"

    # WHEN try to extract this value
    # THEN must fail with MetricUnitError
    with pytest.raises(MetricUnitError, match="Invalid metric unit.*"):
        extract_cloudwatch_metric_unit_value(metric_units, metric_unit_valid_options, unit=unit)


def test_extract_valid_cloudwatch_metric_unit_value():
    metric_units = [unit.value for unit in MetricUnit]
    metric_unit_valid_options = list(MetricUnit.__members__)

    # GIVEN an invalid EMF unit value
    unit = "Count"

    # WHEN try to extract this value
    extracted_unit_value = extract_cloudwatch_metric_unit_value(metric_units, metric_unit_valid_options, unit=unit)

    # THEN value must be extracted
    assert extracted_unit_value == unit


def test_serialize_datadog_tags():
    # GIVEN a dict
    tags = {"project": "powertools", "language": "python310"}
    default_tags = {"project": "powertools-for-lambda", "language": "python311"}

    # WHEN we serialize tags
    tags_output = serialize_datadog_tags(tags, None)

    # WHEN we serialize default tags
    default_tags_output = serialize_datadog_tags(None, default_tags)

    # THEN output must be a list
    assert tags_output == ["project:powertools", "language:python310"]
    assert default_tags_output == ["project:powertools-for-lambda", "language:python311"]


def test_invalid_datadog_metric_name():
    # GIVEN three metrics names with different invalid names
    metric_1 = "1_metric"  # Metric name must not start with number
    metric_2 = "metric_ç"  # Metric name must not contains unicode characters
    metric_3 = "".join(["x" for _ in range(201)])  # Metric name must have less than 200 characters

    # WHEN we try to validate those metrics names
    # THEN must be False
    assert validate_datadog_metric_name(metric_1) is False
    assert validate_datadog_metric_name(metric_2) is False
    assert validate_datadog_metric_name(metric_3) is False


def test_valid_datadog_metric_name():
    # GIVEN a metric with a valid name
    metric = "metric_powertools"  # Metric name must not start with number

    # WHEN we try to validate those metrics names
    # THEN must be True
    assert validate_datadog_metric_name(metric) is True
