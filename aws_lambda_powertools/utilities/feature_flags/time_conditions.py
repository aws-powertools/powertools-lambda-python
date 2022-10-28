from datetime import datetime, timezone
from typing import Dict

from .schema import TimeKeys, TimeValues

HOUR_MIN_SEPARATOR = ":"


def time_range_compare(action: str, values: Dict) -> bool:
    if action == TimeKeys.CURRENT_TIME_UTC.value:
        return _time_range_compare_current_time_utc(action, values)
    elif action == TimeKeys.CURRENT_HOUR_UTC.value:
        return _time_range_compare_current_time_utc(action, values)
    # we assume it passed validation right? so no need to raise an error
    return False


def time_selected_days_compare(action: str, values: Dict) -> bool:
    if action == TimeKeys.CURRENT_DAY_UTC.value:
        return _time_selected_days_current_days_compare(action, values)
    # we assume it passed validation right? so no need to raise an error
    return False


def _time_selected_days_current_days_compare(action: str, values: Dict) -> bool:
    # implement here
    return True


def _time_range_compare_current_time_utc(action: str, values: Dict) -> bool:
    current_time_utc: datetime = datetime.now(timezone.utc)
    start_date = datetime.strptime(values.get(TimeValues.START_TIME, ""), "%Y-%m-%dT%H:%M:%S%z")
    end_date = datetime.strptime(values.get(TimeValues.END_TIME, ""), "%Y-%m-%dT%H:%M:%S%z")
    return current_time_utc >= start_date and current_time_utc <= end_date


def _time_range_compare_current_hour_utc(action: str, values: Dict) -> bool:
    current_time_utc: datetime = datetime.now(timezone.utc)
    start_hour, start_min = values.get(TimeValues.START_TIME, HOUR_MIN_SEPARATOR).split(HOUR_MIN_SEPARATOR)
    end_hour, end_min = values.get(TimeValues.END_TIME, HOUR_MIN_SEPARATOR).split(HOUR_MIN_SEPARATOR)
    return (
        current_time_utc.hour >= int(start_hour)
        and current_time_utc.hour <= int(end_hour)
        and current_time_utc.minute >= int(start_min)
        and current_time_utc.minute <= int(end_min)
    )
