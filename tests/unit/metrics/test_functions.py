import warnings

import pytest

from aws_lambda_powertools.metrics import Metrics
from aws_lambda_powertools.metrics.functions import (
    extract_cloudwatch_metric_resolution_value,
    extract_cloudwatch_metric_unit_value,
)
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.exceptions import (
    MetricResolutionError,
    MetricUnitError,
)
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.metric_properties import MetricResolution, MetricUnit
from aws_lambda_powertools.warnings import PowertoolsUserWarning


@pytest.fixture
def warning_catcher(monkeypatch):
    caught_warnings = []

    def custom_warn(message, category=None, stacklevel=1, source=None):
        caught_warnings.append(PowertoolsUserWarning(message))

    monkeypatch.setattr(warnings, "warn", custom_warn)
    return caught_warnings


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


def test_add_dimension_overwrite_warning(warning_catcher):
    """
    Adds a dimension and then tries to add another with the same name
    but a different value. Verifies if the dimension is updated with
    the new value and  warning is issued when an existing dimension
    is overwritten.
    """
    metrics = Metrics(namespace="TestNamespace")

    # GIVEN default dimension
    dimension_name = "test-dimension"
    value1 = "test-value-1"
    value2 = "test-value-2"

    # WHEN adding the same dimension twice with different values
    metrics.add_dimension(dimension_name, value1)
    metrics.add_dimension(dimension_name, value2)

    # THEN the dimension should be updated with the new value
    assert metrics._dimensions[dimension_name] == value2

    # AND a warning should be issued with the exact message
    expected_warning = f"Dimension '{dimension_name}' has already been added. The previous value will be overwritten."
    assert any(str(w) == expected_warning for w in warning_catcher)
