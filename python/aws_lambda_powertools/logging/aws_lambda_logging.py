"""Microlibrary to simplify logging in AWS Lambda.
Originally taken from https://gitlab.com/hadrien/aws_lambda_logging/
"""
import json
import logging


def json_formatter(obj):
    """Formatter for unserialisable values."""
    return str(obj)


class JsonFormatter(logging.Formatter):
    """AWS Lambda Logging formatter.

    Formats the log message as a JSON encoded string.  If the message is a
    dict it will be used directly.  If the message can be parsed as JSON, then
    the parse d value is used in the output record.
    """

    def __init__(self, **kwargs):
        """Return a JsonFormatter instance.

        The `json_default` kwarg is used to specify a formatter for otherwise
        unserialisable values.  It must not throw.  Defaults to a function that
        coerces the value to a string.

        Other kwargs are used to specify log field format strings.
        """
        datefmt = kwargs.pop("datefmt", None)

        super(JsonFormatter, self).__init__(datefmt=datefmt)
        self.format_dict = {
            "timestamp": "%(asctime)s",
            "level": "%(levelname)s",
            "location": "%(name)s.%(funcName)s:%(lineno)d",
        }
        self.format_dict.update(kwargs)
        self.default_json_formatter = kwargs.pop("json_default", json_formatter)

    def format(self, record):  # noqa: A003
        record_dict = record.__dict__.copy()
        record_dict["asctime"] = self.formatTime(record, self.datefmt)

        log_dict = {k: v % record_dict for k, v in self.format_dict.items() if v}

        if isinstance(record_dict["msg"], dict):
            log_dict["message"] = record_dict["msg"]
        else:
            log_dict["message"] = record.getMessage()

            # Attempt to decode the message as JSON, if so, merge it with the
            # overall message for clarity.
            try:
                log_dict["message"] = json.loads(log_dict["message"])
            except (TypeError, ValueError):
                pass

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            # from logging.Formatter:format
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            log_dict["exception"] = record.exc_text

        json_record = json.dumps(log_dict, default=self.default_json_formatter)

        if hasattr(json_record, "decode"):  # pragma: no cover
            json_record = json_record.decode("utf-8")

        return json_record


def setup(level="DEBUG", formatter_cls=JsonFormatter, boto_level=None, **kwargs):
    """Overall Metadata Formatting."""
    if formatter_cls:  # pragma: no cover
        for handler in logging.root.handlers:
            handler.setFormatter(formatter_cls(**kwargs))

    try:
        logging.root.setLevel(level)
    except ValueError:
        logging.root.error("Invalid log level: %s", level)
        level = "INFO"
        logging.root.setLevel(level)

    if not boto_level:
        boto_level = level

    try:  # pragma: no cover
        logging.getLogger("boto").setLevel(boto_level)
        logging.getLogger("boto3").setLevel(boto_level)
        logging.getLogger("botocore").setLevel(boto_level)
    except ValueError:  # pragma: no cover
        logging.root.error("Invalid log level: %s", boto_level)
