import json
import logging
import os


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
        self.format_dict = dict.fromkeys(kwargs.pop("log_record_order", ["level", "location", "message", "timestamp"]))
        self.reserved_keys = ["timestamp", "level", "location"]
        # Set the date format used by `asctime`
        super(JsonFormatter, self).__init__(datefmt=kwargs.pop("datefmt", None))

        self.format_dict.update(self._build_root_keys(**kwargs))

    def _build_root_keys(self, **kwargs):
        return {
            "level": "%(levelname)s",
            "location": "%(funcName)s:%(lineno)d",
            "timestamp": "%(asctime)s",
            **kwargs,
        }

    @staticmethod
    def _get_latest_trace_id():
        xray_trace_id = os.getenv("_X_AMZN_TRACE_ID")
        trace_id = xray_trace_id.split(";")[0].replace("Root=", "") if xray_trace_id else None

        return trace_id

    def update_formatter(self, **kwargs):
        self.format_dict.update(kwargs)

    def format(self, record):  # noqa: A003
        record_dict = record.__dict__.copy()
        record_dict["asctime"] = self.formatTime(record, self.datefmt)

        log_dict = {}

        for key, value in self.format_dict.items():
            if value and key in self.reserved_keys:
                # converts default logging expr to its record value
                # e.g. '%(asctime)s' to '2020-04-24 09:35:40,698'
                log_dict[key] = value % record_dict
            else:
                log_dict[key] = value

        if isinstance(record_dict["msg"], dict):
            log_dict["message"] = record_dict["msg"]
        else:
            log_dict["message"] = record.getMessage()

            # Attempt to decode the message as JSON, if so, merge it with the
            # overall message for clarity.
            try:
                log_dict["message"] = json.loads(log_dict["message"])
            except (json.decoder.JSONDecodeError, TypeError, ValueError):
                pass

        if record.exc_info and not record.exc_text:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            # from logging.Formatter:format
            record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            log_dict["exception"] = record.exc_text

        # fetch latest X-Ray Trace ID, if any
        log_dict.update({"xray_trace_id": self._get_latest_trace_id()})

        # Filter out top level key with values that are None
        log_dict = {k: v for k, v in log_dict.items() if v is not None}

        return json.dumps(log_dict, default=self.default_json_formatter)
