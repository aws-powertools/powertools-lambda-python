import datetime
import time
import uuid


def _formatted_time(now: datetime.date, fmt: str, timezone_offset: int) -> str:
    """String formatted time with optional timezone offset

    Parameters
    ----------
    now : datetime.date
        Current datetime with zero timezone offset
    fmt : str
        Data format before adding timezone offset
    timezone_offset : int
        Timezone offset in hours, defaults to 0
    Returns
    -------
    str
        Returns string formatted time with optional timezone offset
    """
    if timezone_offset != 0:
        now = now + datetime.timedelta(hours=timezone_offset)

    datetime_str = now.strftime(fmt)
    if fmt.endswith(".%f"):
        datetime_str = datetime_str[:-3]

    if timezone_offset == 0:
        postfix = "Z"
    else:
        postfix = "+" if timezone_offset > 0 else "-"
        postfix += str(abs(timezone_offset)).zfill(2)
        postfix += ":00:00"

    return datetime_str + postfix


def make_id() -> str:
    """ID - A unique identifier for an object. This scalar is serialized like a String but isn't meant to be
    human-readable."""
    return str(uuid.uuid4())


def aws_date(timezone_offset: int = 0) -> str:
    """AWSDate - An extended ISO 8601 date string in the format YYYY-MM-DD.

    Parameters
    ----------
    timezone_offset : int
        Timezone offset, defaults to 0

    Returns
    -------
    str
        Returns current time as AWSDate scalar string with optional timezone offset
    """
    return _formatted_time(datetime.datetime.utcnow(), "%Y-%m-%d", timezone_offset)


def aws_time(timezone_offset: int = 0) -> str:
    """AWSTime - An extended ISO 8601 time string in the format hh:mm:ss.sss.

    Parameters
    ----------
    timezone_offset : int
        Timezone offset, defaults to 0

    Returns
    -------
    str
        Returns current time as AWSTime scalar string with optional timezone offset
    """
    return _formatted_time(datetime.datetime.utcnow(), "%H:%M:%S.%f", timezone_offset)


def aws_datetime(timezone_offset: int = 0) -> str:
    """AWSDateTime - An extended ISO 8601 date and time string in the format YYYY-MM-DDThh:mm:ss.sssZ.

    Parameters
    ----------
    timezone_offset : int
        Timezone offset, defaults to 0

    Returns
    -------
    str
        Returns current time as AWSDateTime scalar string with optional timezone offset
    """
    return _formatted_time(datetime.datetime.utcnow(), "%Y-%m-%dT%H:%M:%S.%f", timezone_offset)


def aws_timestamp() -> int:
    """AWSTimestamp - An integer value representing the number of seconds before or after 1970-01-01-T00:00Z."""
    return int(time.time())
