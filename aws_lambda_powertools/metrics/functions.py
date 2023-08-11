from __future__ import annotations

import re
from typing import Any, Dict, List

from aws_lambda_powertools.metrics.provider.cloudwatch_emf.exceptions import (
    MetricResolutionError,
    MetricUnitError,
)
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.metric_properties import MetricResolution, MetricUnit


def extract_cloudwatch_metric_resolution_value(metric_resolutions: List, resolution: int | MetricResolution) -> int:
    """Return metric value from CloudWatch metric unit whether that's str or MetricResolution enum

    Parameters
    ----------
    unit : Union[int, MetricResolution]
        Metric resolution

    Returns
    -------
    int
        Metric resolution value must be 1 or 60

    Raises
    ------
    MetricResolutionError
        When metric resolution is not supported by CloudWatch
    """
    if isinstance(resolution, MetricResolution):
        return resolution.value

    if isinstance(resolution, int) and resolution in metric_resolutions:
        return resolution

    raise MetricResolutionError(
        f"Invalid metric resolution '{resolution}', expected either option: {metric_resolutions}",  # noqa: E501
    )


def extract_cloudwatch_metric_unit_value(metric_units: List, metric_valid_options: List, unit: str | MetricUnit) -> str:
    """Return metric value from CloudWatch metric unit whether that's str or MetricUnit enum

    Parameters
    ----------
    unit : Union[str, MetricUnit]
        Metric unit

    Returns
    -------
    str
        Metric unit value (e.g. "Seconds", "Count/Second")

    Raises
    ------
    MetricUnitError
        When metric unit is not supported by CloudWatch
    """

    if isinstance(unit, str):
        if unit in metric_valid_options:
            unit = MetricUnit[unit].value

        if unit not in metric_units:
            raise MetricUnitError(
                f"Invalid metric unit '{unit}', expected either option: {metric_valid_options}",
            )

    if isinstance(unit, MetricUnit):
        unit = unit.value

    return unit


def serialize_datadog_tags(metric_tags: Dict[str, Any], default_tags: Dict[str, Any]) -> List[str]:
    """
    Serialize metric tags into a list of formatted strings for Datadog integration.

    This function takes a dictionary of metric-specific tags or default tags.
    It parse these tags and converts them into a list of strings in the format "tag_key:tag_value".

    Parameters
    ----------
    metric_tags: Dict[str, Any]
        A dictionary containing metric-specific tags.
    default_tags: Dict[str, Any]
        A dictionary containing default tags applicable to all metrics.

    Returns:
    -------
    List[str]
        A list of formatted tag strings, each in the "tag_key:tag_value" format.

    Example:
        >>> metric_tags = {'environment': 'production', 'service': 'web'}
        >>> serialize_datadog_tags(metric_tags, None)
        ['environment:production', 'service:web']
    """
    tags = metric_tags or default_tags

    return [f"{tag_key}:{tag_value}" for tag_key, tag_value in tags.items()]


def validate_datadog_metric_name(metric_name: str) -> bool:
    """
    Validate a metric name according to specific requirements.

    Metric names must start with a letter.
    Metric names must only contain ASCII alphanumerics, underscores, and periods.
    Other characters, including spaces, are converted to underscores.
    Unicode is not supported.
    Metric names must not exceed 200 characters. Fewer than 100 is preferred from a UI perspective.

    More information here: https://docs.datadoghq.com/metrics/custom_metrics/#naming-custom-metrics

    Parameters:
    ----------
    metric_name: str
        The metric name to be validated.

    Returns:
    -------
    bool
        True if the metric name is valid, False otherwise.
    """

    # Check if the metric name starts with a letter
    # Check if the metric name contains more than 200 characters
    # Check if the resulting metric name only contains ASCII alphanumerics, underscores, and periods
    if not metric_name[0].isalpha() or len(metric_name) > 200 or not re.match(r"^[a-zA-Z0-9_.]+$", metric_name):
        return False

    return True
