from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter

if TYPE_CHECKING:
    from aws_lambda_powertools.logging.types import LogRecord


class DatadogLogFormatter(LambdaPowertoolsFormatter):
    def __init__(
        self,
        json_serializer: Callable[[LogRecord], str] | None = None,
        json_deserializer: Callable[[dict | str | bool | int | float], str] | None = None,
        json_default: Callable[[Any], Any] | None = None,
        datefmt: str | None = None,
        use_datetime_directive: bool = False,
        log_record_order: list[str] | None = None,
        utc: bool = False,
        use_rfc3339: bool = True,  # NOTE: The only change from our base formatter
        **kwargs,
    ):
        """Datadog formatter to comply with Datadog log parsing

        Changes compared to the default Logger Formatter:

        - timestamp format to use RFC3339 e.g., "2023-05-01T15:34:26.841+0200"


        Parameters
        ----------
        log_record_order : list[str] | None, optional
            _description_, by default None

        Parameters
        ----------
        json_serializer : Callable, optional
            function to serialize `obj` to a JSON formatted `str`, by default json.dumps
        json_deserializer : Callable, optional
            function to deserialize `str`, `bytes`, bytearray` containing a JSON document to a Python `obj`,
            by default json.loads
        json_default : Callable, optional
            function to coerce unserializable values, by default str

            Only used when no custom JSON encoder is set

        datefmt : str, optional
            String directives (strftime) to format log timestamp.

            See https://docs.python.org/3/library/time.html#time.strftime or
        use_datetime_directive: str, optional
            Interpret `datefmt` as a format string for `datetime.datetime.strftime`, rather than
            `time.strftime` - Only useful when used alongside `datefmt`.

            See https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior . This
            also supports a custom %F directive for milliseconds.

        log_record_order : list, optional
            set order of log keys when logging, by default ["level", "location", "message", "timestamp"]

        utc : bool, optional
            set logging timestamp to UTC, by default False to continue to use local time as per stdlib
        use_rfc3339: bool, optional
            Whether to use a popular dateformat that complies with both RFC3339 and ISO8601.
            e.g., 2022-10-27T16:27:43.738+02:00.
        kwargs
            Key-value to persist in all log messages
        """
        super().__init__(
            json_serializer=json_serializer,
            json_deserializer=json_deserializer,
            json_default=json_default,
            datefmt=datefmt,
            use_datetime_directive=use_datetime_directive,
            log_record_order=log_record_order,
            utc=utc,
            use_rfc3339=use_rfc3339,
            **kwargs,
        )
