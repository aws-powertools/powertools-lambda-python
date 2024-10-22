from __future__ import annotations

import inspect
import json
import logging
import os
import time
import traceback
from abc import ABCMeta, abstractmethod
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Iterable

from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import powertools_dev_is_set

if TYPE_CHECKING:
    from aws_lambda_powertools.logging.types import LogRecord, LogStackTrace

RESERVED_LOG_ATTRS = (
    "name",
    "msg",
    "args",
    "level",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "asctime",
    "location",
    "timestamp",
)


class BasePowertoolsFormatter(logging.Formatter, metaclass=ABCMeta):
    @abstractmethod
    def append_keys(self, **additional_keys) -> None:
        raise NotImplementedError()

    def get_current_keys(self) -> dict[str, Any]:
        return {}

    def remove_keys(self, keys: Iterable[str]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def clear_state(self) -> None:
        """Removes any previously added logging keys"""
        raise NotImplementedError()

    # These specific thread-safe methods are necessary to manage shared context in concurrent environments.
    # They prevent race conditions and ensure data consistency across multiple threads.
    def thread_safe_append_keys(self, **additional_keys) -> None:
        raise NotImplementedError()

    def thread_safe_get_current_keys(self) -> dict[str, Any]:
        return {}

    def thread_safe_remove_keys(self, keys: Iterable[str]) -> None:
        raise NotImplementedError()

    def thread_safe_clear_keys(self) -> None:
        """Removes any previously added logging keys in a specific thread"""
        raise NotImplementedError()


class LambdaPowertoolsFormatter(BasePowertoolsFormatter):
    """Powertools for AWS Lambda (Python) Logging formatter.

    Formats the log message as a JSON encoded string. If the message is a
    dict it will be used directly.
    """

    default_time_format = "%Y-%m-%d %H:%M:%S,%F%z"  # '2021-04-17 18:19:57,656+0200'
    custom_ms_time_directive = "%F"
    RFC3339_ISO8601_FORMAT = "%Y-%m-%dT%H:%M:%S.%F%z"  # '2022-10-27T16:27:43.738+02:00'

    def __init__(
        self,
        json_serializer: Callable[[LogRecord], str] | None = None,
        json_deserializer: Callable[[dict | str | bool | int | float], str] | None = None,
        json_default: Callable[[Any], Any] | None = None,
        datefmt: str | None = None,
        use_datetime_directive: bool = False,
        log_record_order: list[str] | None = None,
        utc: bool = False,
        use_rfc3339: bool = False,
        serialize_stacktrace: bool = True,
        **kwargs,
    ) -> None:
        """Return a LambdaPowertoolsFormatter instance.

        The `log_record_order` kwarg is used to specify the order of the keys used in
        the structured json logs. By default the order is: "level", "location", "message", "timestamp",
        "service".

        Other kwargs are used to specify log field format strings.

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
        utc : bool, optional
            set logging timestamp to UTC, by default False to continue to use local time as per stdlib
        use_rfc3339: bool, optional
            Whether to use a popular dateformat that complies with both RFC3339 and ISO8601.
            e.g., 2022-10-27T16:27:43.738+02:00.
        log_record_order : list, optional
            set order of log keys when logging, by default ["level", "location", "message", "timestamp"]
        kwargs
            Key-value to be included in log messages

        """

        self.json_deserializer = json_deserializer or json.loads
        self.json_default = json_default or str
        self.json_indent = (
            constants.PRETTY_INDENT if powertools_dev_is_set() else constants.COMPACT_INDENT
        )  # indented json serialization when in AWS SAM Local
        self.json_serializer = json_serializer or partial(
            json.dumps,
            default=self.json_default,
            separators=(",", ":"),
            indent=self.json_indent,
            ensure_ascii=False,  # see #3474
        )

        self.datefmt = datefmt
        self.use_datetime_directive = use_datetime_directive

        self.utc = utc
        self.log_record_order = log_record_order or ["level", "location", "message", "timestamp"]
        self.log_format = dict.fromkeys(self.log_record_order)  # Set the insertion order for the log messages
        self.update_formatter = self.append_keys  # alias to old method
        self.use_rfc3339_iso8601 = use_rfc3339

        if self.utc:
            self.converter = time.gmtime
        else:
            self.converter = time.localtime

        self.keys_combined = {**self._build_default_keys(), **kwargs}
        self.log_format.update(**self.keys_combined)

        self.serialize_stacktrace = serialize_stacktrace

        super().__init__(datefmt=self.datefmt)

    def serialize(self, log: LogRecord) -> str:
        """Serialize structured log dict to JSON str"""
        return self.json_serializer(log)

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        """Format logging record as structured JSON str"""
        formatted_log = self._extract_log_keys(log_record=record)
        formatted_log["message"] = self._extract_log_message(log_record=record)

        # exception and exception_name fields can be added as extra key
        # in any log level, we try to extract and use them first
        extracted_exception, extracted_exception_name = self._extract_log_exception(log_record=record)
        formatted_log["exception"] = formatted_log.get("exception", extracted_exception)
        formatted_log["exception_name"] = formatted_log.get("exception_name", extracted_exception_name)
        if self.serialize_stacktrace:
            # Generate the traceback from the traceback library
            formatted_log["stack_trace"] = self._serialize_stacktrace(log_record=record)
        formatted_log["xray_trace_id"] = self._get_latest_trace_id()
        formatted_log = self._strip_none_records(records=formatted_log)

        return self.serialize(log=formatted_log)

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        # As of Py3.7, we can infer milliseconds directly from any datetime
        # saving processing time as we can shortcircuit early
        # Maintenance: In V3, we (and Java) should move to this format by default
        # since we've provided enough time for those migrating from std logging
        if self.use_rfc3339_iso8601:
            if self.utc:
                ts_as_datetime = datetime.fromtimestamp(record.created, tz=timezone.utc)
            else:
                ts_as_datetime = datetime.fromtimestamp(record.created).astimezone()

            return ts_as_datetime.isoformat(timespec="milliseconds")  # 2022-10-27T17:42:26.841+0200

        # converts to local/UTC TZ as struct time
        record_ts = self.converter(record.created)

        if datefmt is None:  # pragma: no cover, it'll always be None in std logging, but mypy
            datefmt = self.datefmt

        # NOTE: Python `time.strftime` doesn't provide msec directives
        # so we create a custom one (%F) and replace logging record_ts
        # Reason 2 is that std logging doesn't support msec after TZ
        msecs = "%03d" % record.msecs

        # Datetime format codes is a superset of time format codes
        # therefore we only honour them if explicitly asked
        # by default, those migrating from std logging will use time format codes
        # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        if self.use_datetime_directive and datefmt:
            # record.msecs are microseconds, divide by 1000 to get milliseconds
            timestamp = record.created + record.msecs / 1000

            if self.utc:
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            else:
                dt = datetime.fromtimestamp(timestamp).astimezone()

            custom_fmt = datefmt.replace(self.custom_ms_time_directive, msecs)
            return dt.strftime(custom_fmt)

        # Only time format codes being used
        elif datefmt:
            custom_fmt = datefmt.replace(self.custom_ms_time_directive, msecs)
            return time.strftime(custom_fmt, record_ts)

        # Use default fmt: 2021-05-03 10:20:19,650+0200
        custom_fmt = self.default_time_format.replace(self.custom_ms_time_directive, msecs)
        return time.strftime(custom_fmt, record_ts)

    def append_keys(self, **additional_keys) -> None:
        self.log_format.update(additional_keys)

    def get_current_keys(self) -> dict[str, Any]:
        return self.log_format

    def remove_keys(self, keys: Iterable[str]) -> None:
        for key in keys:
            self.log_format.pop(key, None)

    def clear_state(self) -> None:
        self.log_format = dict.fromkeys(self.log_record_order)
        self.log_format.update(**self.keys_combined)

    # These specific thread-safe methods are necessary to manage shared context in concurrent environments.
    # They prevent race conditions and ensure data consistency across multiple threads.
    def thread_safe_append_keys(self, **additional_keys) -> None:
        # Append additional key-value pairs to the context safely in a thread-safe manner.
        set_context_keys(**additional_keys)

    def thread_safe_get_current_keys(self) -> dict[str, Any]:
        # Retrieve the current context keys safely in a thread-safe manner.
        return _get_context().get()

    def thread_safe_remove_keys(self, keys: Iterable[str]) -> None:
        # Remove specified keys from the context safely in a thread-safe manner.
        remove_context_keys(keys)

    def thread_safe_clear_keys(self) -> None:
        # Clear all keys from the context safely in a thread-safe manner.
        clear_context_keys()

    @staticmethod
    def _build_default_keys() -> dict[str, str]:
        return {
            "level": "%(levelname)s",
            "location": "%(funcName)s:%(lineno)d",
            "timestamp": "%(asctime)s",
        }

    def _get_latest_trace_id(self) -> str | None:
        xray_trace_id_key = self.log_format.get("xray_trace_id", "")
        if xray_trace_id_key is None:
            # key is explicitly disabled; ignore it. e.g., Logger(xray_trace_id=None)
            return None

        xray_trace_id = os.getenv(constants.XRAY_TRACE_ID_ENV)
        return xray_trace_id.split(";")[0].replace("Root=", "") if xray_trace_id else None

    def _extract_log_message(self, log_record: logging.LogRecord) -> dict[str, Any] | str | bool | Iterable:
        """Extract message from log record and attempt to JSON decode it if str

        Parameters
        ----------
        log_record : logging.LogRecord
            Log record to extract message from

        Returns
        -------
        message: dict[str, Any] | str | bool | Iterable
            Extracted message
        """
        message = log_record.msg
        if isinstance(message, dict):
            return message

        if log_record.args:  # logger.info("foo %s", "bar") requires formatting
            return log_record.getMessage()

        if isinstance(message, str):  # could be a JSON string
            try:
                message = self.json_deserializer(message)
            except (json.decoder.JSONDecodeError, TypeError, ValueError):
                pass

        return message

    def _serialize_stacktrace(self, log_record: logging.LogRecord) -> LogStackTrace | None:
        if log_record.exc_info:
            exception_info: LogStackTrace = {
                "type": log_record.exc_info[0].__name__,  # type: ignore
                "value": log_record.exc_info[1],  # type: ignore
                "module": log_record.exc_info[1].__class__.__module__,
                "frames": [],
            }

            exception_info["frames"] = [
                {"file": fs.filename, "line": fs.lineno, "function": fs.name, "statement": fs.line}
                for fs in traceback.extract_tb(log_record.exc_info[2])
            ]

            return exception_info

        return None

    def _extract_log_exception(self, log_record: logging.LogRecord) -> tuple[str, str] | tuple[None, None]:
        """Format traceback information, if available

        Parameters
        ----------
        log_record : logging.LogRecord
            Log record to extract message from

        Returns
        -------
        log_record: tuple[str, str] | tuple[None, None]
            Log record with constant traceback info and exception name
        """
        if log_record.exc_info:
            return self.formatException(log_record.exc_info), log_record.exc_info[0].__name__  # type: ignore

        return None, None

    def _extract_log_keys(self, log_record: logging.LogRecord) -> dict[str, Any]:
        """Extract and parse custom and reserved log keys

        Parameters
        ----------
        log_record : logging.LogRecord
            Log record to extract keys from

        Returns
        -------
        formatted_log: dict[str, Any]
            Structured log as dictionary
        """
        record_dict = log_record.__dict__.copy()
        record_dict["asctime"] = self.formatTime(record=log_record)
        extras = {k: v for k, v in record_dict.items() if k not in RESERVED_LOG_ATTRS}

        formatted_log: dict[str, Any] = {}

        # Iterate over a default or existing log structure
        # then replace any std log attribute e.g. '%(level)s' to 'INFO', '%(process)d to '4773'
        # check if the value is a str if the key is a reserved attribute, the modulo operator only supports string
        # lastly add or replace incoming keys (those added within the constructor or .structure_logs method)
        for key, value in self.log_format.items():
            if value and key in RESERVED_LOG_ATTRS:
                if isinstance(value, str):
                    formatted_log[key] = value % record_dict
                else:
                    raise ValueError(
                        "Logging keys that override reserved log attributes need to be type 'str', "
                        f"instead got '{type(value).__name__}'",
                    )
            else:
                formatted_log[key] = value

        for key, value in _get_context().get().items():
            if value and key in RESERVED_LOG_ATTRS:
                if isinstance(value, str):
                    formatted_log[key] = value % record_dict
                else:
                    raise ValueError(
                        "Logging keys that override reserved log attributes need to be type 'str', "
                        f"instead got '{type(value).__name__}'",
                    )
            else:
                formatted_log[key] = value

        formatted_log.update(**extras)
        return formatted_log

    @staticmethod
    def _strip_none_records(records: dict[str, Any]) -> dict[str, Any]:
        """Remove any key with None as value"""
        return {k: v for k, v in records.items() if v is not None}


JsonFormatter = LambdaPowertoolsFormatter  # alias to previous formatter


# Fetch current and future parameters from PowertoolsFormatter that should be reserved
RESERVED_FORMATTER_CUSTOM_KEYS: list[str] = inspect.getfullargspec(LambdaPowertoolsFormatter).args[1:]

# ContextVar for thread local keys
THREAD_LOCAL_KEYS: ContextVar[dict[str, Any]] = ContextVar("THREAD_LOCAL_KEYS", default={})


def _get_context() -> ContextVar[dict[str, Any]]:
    return THREAD_LOCAL_KEYS


def clear_context_keys() -> None:
    _get_context().set({})


def set_context_keys(**kwargs: dict[str, Any]) -> None:
    context = _get_context()
    context.set({**context.get(), **kwargs})


def remove_context_keys(keys: Iterable[str]) -> None:
    context = _get_context()
    context_values = context.get()

    for k in keys:
        context_values.pop(k, None)

    context.set(context_values)
