from __future__ import annotations

import os
from datetime import datetime

from aws_lambda_powertools.metrics.provider.cloudwatch_emf.exceptions import (
    MetricResolutionError,
    MetricUnitError,
)
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.metric_properties import MetricResolution, MetricUnit
from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import strtobool


def extract_cloudwatch_metric_resolution_value(metric_resolutions: list, resolution: int | MetricResolution) -> int:
    """Return metric value from CloudWatch metric unit whether that's str or MetricResolution enum

    Parameters
    ----------
    resolution : int | MetricResolution
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


def extract_cloudwatch_metric_unit_value(metric_units: list, metric_valid_options: list, unit: str | MetricUnit) -> str:
    """Return metric value from CloudWatch metric unit whether that's str or MetricUnit enum

    Parameters
    ----------
    unit : str | MetricUnit
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


def validate_emf_timestamp(timestamp: int | datetime) -> bool:
    """
    Validates a given timestamp based on CloudWatch Timestamp guidelines.

    Timestamp must meet CloudWatch requirements, otherwise an InvalidTimestampError will be raised.
    See [Timestamps](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html#about_timestamp)
    for valid values.

    Parameters:
    ----------
    timestamp: int | datetime
        Datetime object or epoch time in milliseconds representing the timestamp to validate.

    Returns
    -------
    bool
        Valid or not timestamp values
    """

    if not isinstance(timestamp, (int, datetime)):
        return False

    if isinstance(timestamp, datetime):
        # Converting timestamp to epoch time in milliseconds
        timestamp = int(timestamp.timestamp() * 1000)

    # Consider current timezone when working with date and time
    current_timezone = datetime.now().astimezone().tzinfo

    current_time = int(datetime.now(current_timezone).timestamp() * 1000)
    min_valid_timestamp = current_time - constants.EMF_MAX_TIMESTAMP_PAST_AGE
    max_valid_timestamp = current_time + constants.EMF_MAX_TIMESTAMP_FUTURE_AGE

    return min_valid_timestamp <= timestamp <= max_valid_timestamp


def convert_timestamp_to_emf_format(timestamp: int | datetime) -> int:
    """
    Converts a timestamp to EMF compatible format.

    Parameters
    ----------
    timestamp: int | datetime
        The timestamp to convert. If already in epoch milliseconds format, returns it as is.
        If datetime object, converts it to milliseconds since Unix epoch.

    Returns:
    --------
    int
        The timestamp converted to EMF compatible format (milliseconds since Unix epoch).
    """
    if isinstance(timestamp, int):
        return timestamp

    try:
        return int(round(timestamp.timestamp() * 1000))
    except AttributeError:
        # If this point is reached, it indicates timestamp is not a datetime object
        # Returning zero represents the initial date of epoch time,
        # which will be skipped by Amazon CloudWatch.
        return 0


def is_metrics_disabled() -> bool:
    """
    Determine if metrics should be disabled based on environment variables.

    Returns:
        bool: True if metrics are disabled, False otherwise.

    Rules:
    - If POWERTOOLS_DEV is True and POWERTOOLS_METRICS_DISABLED is True: Disable metrics
    - If POWERTOOLS_METRICS_DISABLED is True: Disable metrics
    - If POWERTOOLS_DEV is True and POWERTOOLS_METRICS_DISABLED is not set: Disable metrics
    """

    is_dev_mode = strtobool(os.getenv(constants.POWERTOOLS_DEV_ENV, "false"))
    is_metrics_disabled = strtobool(os.getenv(constants.METRICS_DISABLED_ENV, "false"))

    disable_conditions = [
        is_metrics_disabled,
        is_metrics_disabled and is_dev_mode,
        is_dev_mode and os.getenv(constants.METRICS_DISABLED_ENV) is None,
    ]

    return any(disable_conditions)
