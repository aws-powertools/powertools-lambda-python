import json
import logging
import os
from typing import Dict, Iterable, Optional, Union

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


class JsonFormatter(logging.Formatter):
    """AWS Lambda Logging formatter.

    Formats the log message as a JSON encoded string.  If the message is a
    dict it will be used directly.  If the message can be parsed as JSON, then
    the parse d value is used in the output record.

    Originally taken from https://gitlab.com/hadrien/aws_lambda_logging/

    """

    def __init__(self, **kwargs):
        """Return a JsonFormatter instance.

        The `json_default` kwarg is used to specify a formatter for otherwise
        unserializable values.  It must not throw.  Defaults to a function that
        coerces the value to a string.

        The `log_record_order` kwarg is used to specify the order of the keys used in
        the structured json logs. By default the order is: "level", "location", "message", "timestamp",
        "service" and "sampling_rate".

        Other kwargs are used to specify log field format strings.
        """
        # Set the default unserializable function, by default values will be cast as str.
        self.default_json_formatter = kwargs.pop("json_default", str)
        # Set the insertion order for the log messages
        self.log_format = dict.fromkeys(kwargs.pop("log_record_order", ["level", "location", "message", "timestamp"]))
        self.reserved_keys = ["timestamp", "level", "location"]
        # Set the date format used by `asctime`
        super(JsonFormatter, self).__init__(datefmt=kwargs.pop("datefmt", None))

        self.log_format.update(self._build_root_keys(**kwargs))

    @staticmethod
    def _build_root_keys(**kwargs):
        return {
            "level": "%(levelname)s",
            "location": "%(funcName)s:%(lineno)d",
            "timestamp": "%(asctime)s",
            **kwargs,
        }

    @staticmethod
    def _get_latest_trace_id():
        xray_trace_id = os.getenv(constants.XRAY_TRACE_ID_ENV)
        return xray_trace_id.split(";")[0].replace("Root=", "") if xray_trace_id else None

    def update_formatter(self, **kwargs):
        self.log_format.update(kwargs)

    @staticmethod
    def _extract_log_message(log_record: logging.LogRecord) -> Union[Dict, str, bool, Iterable]:
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

        # Attempt to decode non-str messages e.g. msg = '{"x": "y"}'
        try:
            message = json.loads(log_record.msg)
        except (json.decoder.JSONDecodeError, TypeError, ValueError):
            pass

        return message

    def _extract_log_exception(self, log_record: logging.LogRecord) -> Optional[str]:
        """Format traceback information, if available

        Parameters
        ----------
        log_record : logging.LogRecord
            Log record to extract message from

        Returns
        -------
        log_record: Optional[str]
            Log record with constant traceback info
        """
        if log_record.exc_info:
            return self.formatException(log_record.exc_info)

        return None

    def _extract_log_exception_name(self, log_record: logging.LogRecord) -> Optional[str]:
        """Extract the exception name, if available

        Parameters
        ----------
        log_record : logging.LogRecord
            Log record to extract exception name from

        Returns
        -------
        log_record: Optional[str]
            Log record with exception name
        """
        if log_record.exc_info:
            return log_record.exc_info[0].__name__

        return None

    def _extract_log_keys(self, log_record: logging.LogRecord) -> Dict:
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
        record_dict = log_record.__dict__.copy()  # has extra kwargs we are after
        record_dict["asctime"] = self.formatTime(log_record, self.datefmt)

        formatted_log = {}

        # We have to iterate over a default or existing log structure
        # then replace any logging expression for reserved keys e.g. '%(level)s' to 'INFO'
        # and lastly add or replace incoming keys (those added within the constructor or .structure_logs method)
        for key, value in self.log_format.items():
            if value and key in self.reserved_keys:
                formatted_log[key] = value % record_dict
            else:
                formatted_log[key] = value

        # pick up extra keys when logging a new message e.g. log.info("my message", extra={"additional_key": "value"}
        # these messages will be added to the root of the final structure not within `message` key
        for key, value in record_dict.items():
            if key not in STD_LOGGING_KEYS:
                formatted_log[key] = value

        return formatted_log

    def format(self, record):  # noqa: A003
        formatted_log = self._extract_log_keys(log_record=record)
        formatted_log["message"] = self._extract_log_message(log_record=record)
        formatted_log["exception_name"] = self._extract_log_exception_name(log_record=record)
        formatted_log["exception"] = self._extract_log_exception(log_record=record)
        formatted_log.update({"xray_trace_id": self._get_latest_trace_id()})  # fetch latest Trace ID, if any

        # Filter out top level key with values that are None
        formatted_log = {k: v for k, v in formatted_log.items() if v is not None}

        return json.dumps(formatted_log, default=self.default_json_formatter)
