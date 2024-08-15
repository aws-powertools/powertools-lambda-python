from __future__ import annotations

from datetime import datetime, tzinfo
from typing import Any

from dateutil.tz import gettz

from aws_lambda_powertools.utilities.feature_flags.constants import HOUR_MIN_SEPARATOR
from aws_lambda_powertools.utilities.feature_flags.schema import ModuloRangeValues, TimeValues


def _get_now_from_timezone(timezone: tzinfo | None) -> datetime:
    """
    Returns now in the specified timezone. Defaults to UTC if not present.
    At this stage, we already validated that the passed timezone string is valid, so we assume that
    gettz() will return a tzinfo object.
    """
    timezone = gettz("UTC") if timezone is None else timezone
    return datetime.now(timezone)


def compare_days_of_week(context_value: Any, condition_value: dict) -> bool:
    timezone_name = condition_value.get(TimeValues.TIMEZONE.value, "UTC")

    # %A = Weekday as locale’s full name.
    current_day = _get_now_from_timezone(gettz(timezone_name)).strftime("%A").upper()

    days = condition_value.get(TimeValues.DAYS.value, [])
    return current_day in days


def compare_datetime_range(context_value: Any, condition_value: dict) -> bool:
    timezone_name = condition_value.get(TimeValues.TIMEZONE.value, "UTC")
    timezone = gettz(timezone_name)
    current_time: datetime = _get_now_from_timezone(timezone)

    start_date_str = condition_value.get(TimeValues.START.value, "")
    end_date_str = condition_value.get(TimeValues.END.value, "")

    # Since start_date and end_date doesn't include timezone information, we mark the timestamp
    # with the same timezone as the current_time. This way all the 3 timestamps will be on
    # the same timezone.
    start_date = datetime.fromisoformat(start_date_str).replace(tzinfo=timezone)
    end_date = datetime.fromisoformat(end_date_str).replace(tzinfo=timezone)
    return start_date <= current_time <= end_date


def compare_time_range(context_value: Any, condition_value: dict) -> bool:
    timezone_name = condition_value.get(TimeValues.TIMEZONE.value, "UTC")
    current_time: datetime = _get_now_from_timezone(gettz(timezone_name))

    start_hour, start_min = condition_value.get(TimeValues.START.value, "").split(HOUR_MIN_SEPARATOR)
    end_hour, end_min = condition_value.get(TimeValues.END.value, "").split(HOUR_MIN_SEPARATOR)

    start_time = current_time.replace(hour=int(start_hour), minute=int(start_min))
    end_time = current_time.replace(hour=int(end_hour), minute=int(end_min))

    if int(end_hour) < int(start_hour):
        # When the end hour is smaller than start hour, it means we are crossing a day's boundary.
        # In this case we need to assert that current_time is **either** on one side or the other side of the boundary
        #
        # ┌─────┐                                    ┌─────┐                                  ┌─────┐
        # │20.00│                                    │00.00│                                  │04.00│
        # └─────┘                                    └─────┘                                  └─────┘
        #    ───────────────────────────────────────────┬─────────────────────────────────────────▶
        #    ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │ ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
        #                                             │ │                                        │
        #    │           either this area               │ │             or this area
        #                                             │ │                                        │
        #    └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │ └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
        #                                               │

        return (start_time <= current_time) or (current_time <= end_time)
    else:
        # In normal circumstances, we need to assert **both** conditions
        return start_time <= current_time <= end_time


def compare_modulo_range(context_value: int, condition_value: dict) -> bool:
    """
    Returns for a given context 'a' and modulo condition 'b' -> b.start <= a % b.base <= b.end
    """
    base = condition_value.get(ModuloRangeValues.BASE.value, 1)
    start = condition_value.get(ModuloRangeValues.START.value, 1)
    end = condition_value.get(ModuloRangeValues.END.value, 1)

    return start <= context_value % base <= end


def compare_any_in_list(context_value: list, condition_value: list) -> bool:
    """Comparator for ANY_IN_VALUE action

    Parameters
    ----------
    context_value : list
        user-defined context for flag evaluation
    condition_value : list
        schema value available for condition being evaluated

    Returns
    -------
    bool
        Whether any list item in context_value is available in condition_value
    """
    if not isinstance(context_value, list):
        raise ValueError("Context provided must be a list. Unable to compare ANY_IN_VALUE action.")

    return any(key in condition_value for key in context_value)


def compare_all_in_list(context_value: list, condition_value: list) -> bool:
    """Comparator for ALL_IN_VALUE action

    Parameters
    ----------
    context_value : list
        user-defined context for flag evaluation
    condition_value : list
        schema value available for condition being evaluated

    Returns
    -------
    bool
        Whether all list items in context_value are available in condition_value
    """
    if not isinstance(context_value, list):
        raise ValueError("Context provided must be a list. Unable to compare ALL_IN_VALUE action.")

    return all(key in condition_value for key in context_value)


def compare_none_in_list(context_value: list, condition_value: list) -> bool:
    """Comparator for NONE_IN_VALUE action

    Parameters
    ----------
    context_value : list
        user-defined context for flag evaluation
    condition_value : list
        schema value available for condition being evaluated

    Returns
    -------
    bool
        Whether list items in context_value are **not** available in condition_value
    """
    if not isinstance(context_value, list):
        raise ValueError("Context provided must be a list. Unable to compare NONE_IN_VALUE action.")

    return all(key not in condition_value for key in context_value)
