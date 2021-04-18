import json
import logging
import os
import time
from functools import partial
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

from ..shared import constants

STD_LOGGING_KEYS = (
    "name",
    "msg",
    "args",
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
)


class LambdaPowertoolsFormatter(logging.Formatter):
    """AWS Lambda Powertools Logging formatter.

    Formats the log message as a JSON encoded string. If the message is a
    dict it will be used directly.
    """

    default_time_format = "%Y-%m-%d %H:%M:%S.%F%z"  # '2021-04-17 18:19:57.656+0200'
    custom_ms_time_directive = "%F"

    def __init__(
        self,
        json_encoder: Optional[Callable[[Any], Any]] = None,
        json_decoder: Optional[Callable[[Any], Any]] = None,
        json_default: Optional[Callable[[Any], Any]] = None,
        datefmt: str = None,
        log_record_order: List = None,
        utc: bool = False,
        **kwargs
    ):
        """Return a LambdaPowertoolsFormatter instance.

        The `log_record_order` kwarg is used to specify the order of the keys used in
        the structured json logs. By default the order is: "level", "location", "message", "timestamp",
        "service" and "sampling_rate".

        Other kwargs are used to specify log field format strings.

        Parameters
        ----------
        json_encoder : Callable, optional
            A function to serialize `obj` to a JSON formatted `str`, by default json.dumps
        json_decoder : Callable, optional
            A function to deserialize `str`, `bytes`, bytearray` containing a JSON document to a Python `obj`,
            by default json.loads
        json_default : Callable, optional
            A function to coercer unserializable values, by default str

            Only used when no custom JSON encoder is set

        datefmt : str, optional
            String directives (strftime) to format log timestamp

            See https://docs.python.org/3/library/time.html#time.strftime
        utc : bool, optional
            Set logging timestamp to UTC, by default False to continue to use local time as per stdlib
        kwargs
            Key-value to be included in log messages

        Examples
        --------
        Create examples

        Add example of standard log attributes that use str interpolation e.g. %(process)d
        Add example of JSON default fn for unserializable values
        Add example for UTC
        """
        self.json_decoder = json_decoder or json.loads
        self.json_default = json_default or str
        self.json_encoder = json_encoder or partial(json.dumps, default=self.json_default, separators=(",", ":"))
        self.datefmt = datefmt
        self.utc = utc
        self.log_record_order = log_record_order or ["level", "location", "message", "timestamp"]
        self.log_format = dict.fromkeys(self.log_record_order)  # Set the insertion order for the log messages

        if self.utc:
            self.converter = time.gmtime

        super(LambdaPowertoolsFormatter, self).__init__(datefmt=self.datefmt)

        keys_combined = {**self._build_default_keys(), **kwargs}
        self.log_format.update(**keys_combined)

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

    def update_formatter(self, **kwargs):
        self.log_format.update(kwargs)

    def _extract_log_message(self, log_record: logging.LogRecord) -> Union[Dict, str, bool, Iterable]:
        """Extract message from log record and attempt to JSON decode it

        Parameters
        ----------
        log_record : logging.LogRecord
            Log record to extract message from

        Returns
        -------
        message: Union[Dict, str, bool, Iterable]
            Extracted message
        """
        if isinstance(log_record.msg, dict):
            return log_record.msg

        message: str = log_record.getMessage()

        try:
            message = self.json_decoder(log_record.msg)
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
            return self.formatException(log_record.exc_info), log_record.exc_info[0].__name__

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
        record_dict["asctime"] = self.formatTime(record=log_record, datefmt=self.datefmt)
        extras = {k: v for k, v in record_dict.items() if k not in STD_LOGGING_KEYS}

        formatted_log = {**extras}

        # Iterate over a default or existing log structure
        # then replace any std log attribute e.g. '%(level)s' to 'INFO', '%(process)d to '4773'
        # lastly add or replace incoming keys (those added within the constructor or .structure_logs method)
        for key, value in self.log_format.items():
            if isinstance(value, str) and value.startswith("%("):
                formatted_log[key] = value % record_dict
            else:
                formatted_log[key] = value

        return formatted_log

    @staticmethod
    def _strip_none_records(records: Dict[str, Any]) -> Dict[str, Any]:
        """Remove any key with None as value"""
        return {k: v for k, v in records.items() if v is not None}

    def format(self, record):  # noqa: A003
        formatted_log = self._extract_log_keys(log_record=record)
        formatted_log["message"] = self._extract_log_message(log_record=record)
        formatted_log["exception"], formatted_log["exception_name"] = self._extract_log_exception(log_record=record)
        formatted_log["xray_trace_id"] = self._get_latest_trace_id()
        formatted_log = self._strip_none_records(records=formatted_log)

        return self.json_encoder(formatted_log)

    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        # NOTE: Pyhton time.strftime doesn't provide msec directives
        # so we create a custom one (%F) and replace logging record ts
        # Reason 2 is that std logging doesn't support msec after TZ
        record_ts = self.converter(record.created)
        if datefmt:
            ts_formatted = time.strftime(datefmt, record_ts)
        else:
            msec = "%03d" % record.msecs
            custom_fmt = self.default_time_format.replace(self.custom_ms_time_directive, msec)
            ts_formatted = time.strftime(custom_fmt, record_ts)
        return ts_formatted


JsonFormatter = LambdaPowertoolsFormatter  # alias to previous formatter
