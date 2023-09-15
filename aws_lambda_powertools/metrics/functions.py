from __future__ import annotations

from aws_lambda_powertools.metrics.provider.cloudwatch_emf.exceptions import (
    MetricResolutionError,
    MetricUnitError,
)
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.metric_properties import MetricResolution, MetricUnit
from aws_lambda_powertools.shared.types import List


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
