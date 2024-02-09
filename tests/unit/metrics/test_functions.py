import pytest

from aws_lambda_powertools.metrics.functions import (
    extract_cloudwatch_metric_resolution_value,
    extract_cloudwatch_metric_unit_value,
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
