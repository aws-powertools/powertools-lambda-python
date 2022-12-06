from datetime import datetime, timezone
from typing import Dict, List

from .schema import HOUR_MIN_SEPARATOR, TimeValues


def _get_utc_time_now() -> datetime:
    return datetime.now(timezone.utc)


def compare_utc_days_of_week(action: str, values: List[str]) -> bool:
    current_day = _get_utc_time_now().strftime("%A").upper()
    return current_day in values


def compare_utc_datetime_range(action: str, values: Dict) -> bool:
    current_time_utc: datetime = _get_utc_time_now()

    # python < 3.11 don't support Z as a timezone on datetime.fromisoformat,
    # so we replace any Z with the equivalent "+00:00
    start_date_str = values.get(TimeValues.START.value, "").replace("Z", "+00:00")
    end_date_str = values.get(TimeValues.END.value, "").replace("Z", "+00:00")

    start_date = datetime.fromisoformat(start_date_str)
    end_date = datetime.fromisoformat(end_date_str)
    return start_date <= current_time_utc <= end_date


def compare_utc_time_range(action: str, values: Dict) -> bool:
    current_time_utc: datetime = _get_utc_time_now()
    start_hour, start_min = values.get(TimeValues.START.value, "").split(HOUR_MIN_SEPARATOR)
    end_hour, end_min = values.get(TimeValues.END.value, "").split(HOUR_MIN_SEPARATOR)
    return (
        current_time_utc.hour >= int(start_hour)
        and current_time_utc.hour <= int(end_hour)
        and current_time_utc.minute >= int(start_min)
        and current_time_utc.minute <= int(end_min)
    )
