from __future__ import annotations

from typing import Any, Callable

from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter


class DatadogLogFormatter(LambdaPowertoolsFormatter):
    def __init__(
        self,
        json_serializer: Callable[[dict], str] | None = None,
        json_deserializer: Callable[[dict | str | bool | int | float], str] | None = None,
        json_default: Callable[[Any], Any] | None = None,
        datefmt: str | None = None,
        use_datetime_directive: bool = False,
        log_record_order: list[str] | None = None,
        utc: bool = False,
        use_rfc3339: bool = True,
        **kwargs,
    ):
        super().__init__(
            json_serializer,
            json_deserializer,
            json_default,
            datefmt,
            use_datetime_directive,
            log_record_order,
            utc,
            use_rfc3339,
            **kwargs,
        )
