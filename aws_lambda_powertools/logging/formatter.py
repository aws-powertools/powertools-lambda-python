import inspect
import json
import logging
import os
import time
from abc import ABCMeta, abstractmethod
from datetime import datetime, timezone
from functools import partial
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

from ..shared import constants
from ..shared.functions import powertools_dev_is_set

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
    def append_keys(self, **additional_keys):
        raise NotImplementedError()

    def remove_keys(self, keys: Iterable[str]):
        raise NotImplementedError()

    @abstractmethod
    def clear_state(self):
        """Removes any previously added logging keys"""
        raise NotImplementedError()


class LambdaPowertoolsFormatter(BasePowertoolsFormatter):
    """AWS Lambda Powertools Logging formatter.

    Formats the log message as a JSON encoded string. If the message is a
    dict it will be used directly.
    """

    default_time_format = "%Y-%m-%d %H:%M:%S,%F%z"  # '2021-04-17 18:19:57,656+0200'
    custom_ms_time_directive = "%F"

    def __init__(
        self,
        json_serializer: Optional[Callable[[Dict], str]] = None,
        json_deserializer: Optional[Callable[[Union[Dict, str, bool, int, float]], str]] = None,
        json_default: Optional[Callable[[Any], Any]] = None,
        datefmt: Optional[str] = None,
        use_datetime_directive: bool = False,
        log_record_order: Optional[List[str]] = None,
        utc: bool = False,
        **kwargs,
    ):
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
            json.dumps, default=self.json_default, separators=(",", ":"), indent=self.json_indent
        )

        self.datefmt = datefmt
        self.use_datetime_directive = use_datetime_directive

        self.utc = utc
        self.log_record_order = log_record_order or ["level", "location", "message", "timestamp"]
        self.log_format = dict.fromkeys(self.log_record_order)  # Set the insertion order for the log messages
        self.update_formatter = self.append_keys  # alias to old method

        if self.utc:
            self.converter = time.gmtime  # type: ignore

        super(LambdaPowertoolsFormatter, self).__init__(datefmt=self.datefmt)

        self.keys_combined = {**self._build_default_keys(), **kwargs}
        self.log_format.update(**self.keys_combined)

    def serialize(self, log: Dict) -> str:
        """Serialize structured log dict to JSON str"""
        return self.json_serializer(log)

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        """Format logging record as structured JSON str"""
        formatted_log = self._extract_log_keys(log_record=record)
        formatted_log["message"] = self._extract_log_message(log_record=record)
        formatted_log["exception"], formatted_log["exception_name"] = self._extract_log_exception(log_record=record)
        formatted_log["xray_trace_id"] = self._get_latest_trace_id()
        formatted_log = self._strip_none_records(records=formatted_log)

        return self.serialize(log=formatted_log)

    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        record_ts = self.converter(record.created)  # type: ignore

        if datefmt is None:  # pragma: no cover, it'll always be None in std logging, but mypy
            datefmt = self.datefmt

        # NOTE: Python `time.strftime` doesn't provide msec directives
        # so we create a custom one (%F) and replace logging record ts
        # Reason 2 is that std logging doesn't support msec after TZ
        msecs = "%03d" % record.msecs

        # Datetime format codes might be optionally used
        # however it only makes a difference if `datefmt` is passed
        # since format codes are the same except %f
        if self.use_datetime_directive and datefmt:
            # record.msecs are microseconds, divide by 1000 and we get milliseconds
            timestamp = record.created + record.msecs / 1000

            if self.utc:
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            else:
                # make sure local timezone is included
                dt = datetime.fromtimestamp(timestamp).astimezone()

            custom_fmt = datefmt.replace(self.custom_ms_time_directive, msecs)
            return dt.strftime(custom_fmt)

        elif datefmt:
            custom_fmt = datefmt.replace(self.custom_ms_time_directive, msecs)
            return time.strftime(custom_fmt, record_ts)

        custom_fmt = self.default_time_format.replace(self.custom_ms_time_directive, msecs)
        return time.strftime(custom_fmt, record_ts)

    def append_keys(self, **additional_keys):
        self.log_format.update(additional_keys)

    def remove_keys(self, keys: Iterable[str]):
        for key in keys:
            self.log_format.pop(key, None)

    def clear_state(self):
        self.log_format = dict.fromkeys(self.log_record_order)
        self.log_format.update(**self.keys_combined)

    @staticmethod
    def _build_default_keys():
        return {
            "level": "%(levelname)s",
            "location": "%(funcName)s:%(lineno)d",
            "timestamp": "%(asctime)s",
        }

    @staticmethod
    def _get_latest_trace_id():
        xray_trace_id = os.getenv(constants.XRAY_TRACE_ID_ENV)
        return xray_trace_id.split(";")[0].replace("Root=", "") if xray_trace_id else None

    def _extract_log_message(self, log_record: logging.LogRecord) -> Union[Dict[str, Any], str, bool, Iterable]:
        """Extract message from log record and attempt to JSON decode it if str

        Parameters
        ----------
        log_record : logging.LogRecord
            Log record to extract message from

        Returns
        -------
        message: Union[Dict, str, bool, Iterable]
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

    def _extract_log_exception(self, log_record: logging.LogRecord) -> Union[Tuple[str, str], Tuple[None, None]]:
        """Format traceback information, if available

        Parameters
        ----------
        log_record : logging.LogRecord
            Log record to extract message from

        Returns
        -------
        log_record: Optional[Tuple[str, str]]
            Log record with constant traceback info and exception name
        """
        if log_record.exc_info:
            return self.formatException(log_record.exc_info), log_record.exc_info[0].__name__  # type: ignore

        return None, None

    def _extract_log_keys(self, log_record: logging.LogRecord) -> Dict[str, Any]:
        """Extract and parse custom and reserved log keys

        Parameters
        ----------
        log_record : logging.LogRecord
            Log record to extract keys from

        Returns
        -------
        formatted_log: Dict
            Structured log as dictionary
        """
        record_dict = log_record.__dict__.copy()
        record_dict["asctime"] = self.formatTime(record=log_record)
        extras = {k: v for k, v in record_dict.items() if k not in RESERVED_LOG_ATTRS}

        formatted_log = {}

        # Iterate over a default or existing log structure
        # then replace any std log attribute e.g. '%(level)s' to 'INFO', '%(process)d to '4773'
        # lastly add or replace incoming keys (those added within the constructor or .structure_logs method)
        for key, value in self.log_format.items():
            if value and key in RESERVED_LOG_ATTRS:
                formatted_log[key] = value % record_dict
            else:
                formatted_log[key] = value

        formatted_log.update(**extras)
        return formatted_log

    @staticmethod
    def _strip_none_records(records: Dict[str, Any]) -> Dict[str, Any]:
        """Remove any key with None as value"""
        return {k: v for k, v in records.items() if v is not None}


JsonFormatter = LambdaPowertoolsFormatter  # alias to previous formatter


# Fetch current and future parameters from PowertoolsFormatter that should be reserved
RESERVED_FORMATTER_CUSTOM_KEYS: List[str] = inspect.getfullargspec(LambdaPowertoolsFormatter).args[1:]
