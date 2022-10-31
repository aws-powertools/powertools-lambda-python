import functools
import inspect
import io
import logging
import os
import random
import sys
import traceback
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    TypeVar,
    Union,
)

import jmespath

from ..shared import constants
from ..shared.functions import resolve_env_var_choice, resolve_truthy_env_var_choice
from .exceptions import InvalidLoggerSamplingRateError
from .filters import SuppressFilter
from .formatter import (
    RESERVED_FORMATTER_CUSTOM_KEYS,
    BasePowertoolsFormatter,
    LambdaPowertoolsFormatter,
)
from .lambda_context import build_lambda_context_model

logger = logging.getLogger(__name__)

is_cold_start = True

PowertoolsFormatter = TypeVar("PowertoolsFormatter", bound=BasePowertoolsFormatter)


def _is_cold_start() -> bool:
    """Verifies whether is cold start

    Returns
    -------
    bool
        cold start bool value
    """
    cold_start = False

    global is_cold_start
    if is_cold_start:
        cold_start = is_cold_start
        is_cold_start = False

    return cold_start


# PyCharm does not support autocomplete via getattr
# so we need to return to subclassing removed in #97
# All methods/properties continue to be proxied to inner logger
# https://github.com/awslabs/aws-lambda-powertools-python/issues/107
# noinspection PyRedeclaration
class Logger(logging.Logger):  # lgtm [py/missing-call-to-init]
    """Creates and setups a logger to format statements in JSON.

    Includes service name and any additional key=value into logs
    It also accepts both service name or level explicitly via env vars

    Environment variables
    ---------------------
    POWERTOOLS_SERVICE_NAME : str
        service name
    LOG_LEVEL: str
        logging level (e.g. INFO, DEBUG)
    POWERTOOLS_LOGGER_SAMPLE_RATE: float
        sampling rate ranging from 0 to 1, 1 being 100% sampling

    Parameters
    ----------
    service : str, optional
        service name to be appended in logs, by default "service_undefined"
    level : str, int optional
        logging.level, by default "INFO"
    child: bool, optional
        create a child Logger named <service>.<caller_file_name>, False by default
    sample_rate: float, optional
        sample rate for debug calls within execution context defaults to 0.0
    stream: sys.stdout, optional
        valid output for a logging stream, by default sys.stdout
    logger_formatter: PowertoolsFormatter, optional
        custom logging formatter that implements PowertoolsFormatter
    logger_handler: logging.Handler, optional
        custom logging handler e.g. logging.FileHandler("file.log")

    Parameters propagated to LambdaPowertoolsFormatter
    --------------------------------------------------
    datefmt: str, optional
        String directives (strftime) to format log timestamp using `time`, by default it uses 2021-05-03 11:47:12,494+0200. # noqa: E501
    use_datetime_directive: bool, optional
        Interpret `datefmt` as a format string for `datetime.datetime.strftime`, rather than
        `time.strftime`.

        See https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior . This
        also supports a custom %F directive for milliseconds.
    use_rfc3339: bool, optional
        Whether to use a popular date format that complies with both RFC3339 and ISO8601.
        e.g., 2022-10-27T16:27:43.738+02:00.
    json_serializer : Callable, optional
        function to serialize `obj` to a JSON formatted `str`, by default json.dumps
    json_deserializer : Callable, optional
        function to deserialize `str`, `bytes`, bytearray` containing a JSON document to a Python `obj`,
        by default json.loads
    json_default : Callable, optional
        function to coerce unserializable values, by default `str()`

        Only used when no custom formatter is set
    utc : bool, optional
        set logging timestamp to UTC, by default False to continue to use local time as per stdlib
    log_record_order : list, optional
        set order of log keys when logging, by default ["level", "location", "message", "timestamp"]

    Example
    -------
    **Setups structured logging in JSON for Lambda functions with explicit service name**

        >>> from aws_lambda_powertools import Logger
        >>> logger = Logger(service="payment")
        >>>
        >>> def handler(event, context):
                logger.info("Hello")

    **Setups structured logging in JSON for Lambda functions using env vars**

        $ export POWERTOOLS_SERVICE_NAME="payment"
        $ export POWERTOOLS_LOGGER_SAMPLE_RATE=0.01 # 1% debug sampling
        >>> from aws_lambda_powertools import Logger
        >>> logger = Logger()
        >>>
        >>> def handler(event, context):
                logger.info("Hello")

    **Append payment_id to previously setup logger**

        >>> from aws_lambda_powertools import Logger
        >>> logger = Logger(service="payment")
        >>>
        >>> def handler(event, context):
                logger.append_keys(payment_id=event["payment_id"])
                logger.info("Hello")

    **Create child Logger using logging inheritance via child param**

        >>> # app.py
        >>> import another_file
        >>> from aws_lambda_powertools import Logger
        >>> logger = Logger(service="payment")
        >>>
        >>> # another_file.py
        >>> from aws_lambda_powertools import Logger
        >>> logger = Logger(service="payment", child=True)

    **Logging in UTC timezone**

        >>> # app.py
        >>> import logging
        >>> from aws_lambda_powertools import Logger
        >>>
        >>> logger = Logger(service="payment", utc=True)

    **Brings message as the first key in log statements**

        >>> # app.py
        >>> import logging
        >>> from aws_lambda_powertools import Logger
        >>>
        >>> logger = Logger(service="payment", log_record_order=["message"])

    **Logging to a file instead of standard output for testing**

        >>> # app.py
        >>> import logging
        >>> from aws_lambda_powertools import Logger
        >>>
        >>> logger = Logger(service="payment", logger_handler=logging.FileHandler("log.json"))

    Raises
    ------
    InvalidLoggerSamplingRateError
        When sampling rate provided is not a float
    """

    def __init__(
        self,
        service: Optional[str] = None,
        level: Union[str, int, None] = None,
        child: bool = False,
        sampling_rate: Optional[float] = None,
        stream: Optional[IO[str]] = None,
        logger_formatter: Optional[PowertoolsFormatter] = None,
        logger_handler: Optional[logging.Handler] = None,
        json_serializer: Optional[Callable[[Dict], str]] = None,
        json_deserializer: Optional[Callable[[Union[Dict, str, bool, int, float]], str]] = None,
        json_default: Optional[Callable[[Any], Any]] = None,
        datefmt: Optional[str] = None,
        use_datetime_directive: bool = False,
        log_record_order: Optional[List[str]] = None,
        utc: bool = False,
        use_rfc3339: bool = False,
        **kwargs,
    ):
        self.service = resolve_env_var_choice(
            choice=service, env=os.getenv(constants.SERVICE_NAME_ENV, "service_undefined")
        )
        self.sampling_rate = resolve_env_var_choice(
            choice=sampling_rate, env=os.getenv(constants.LOGGER_LOG_SAMPLING_RATE)
        )
        self.child = child
        self.logger_formatter = logger_formatter
        self.logger_handler = logger_handler or logging.StreamHandler(stream)
        self.log_level = self._get_log_level(level)
        self._is_deduplication_disabled = resolve_truthy_env_var_choice(
            env=os.getenv(constants.LOGGER_LOG_DEDUPLICATION_ENV, "false")
        )
        self._default_log_keys = {"service": self.service, "sampling_rate": self.sampling_rate}
        self._logger = self._get_logger()

        # NOTE: This is primarily to improve UX, so IDEs can autocomplete LambdaPowertoolsFormatter options
        # previously, we masked all of them as kwargs thus limiting feature discovery
        formatter_options = {
            "json_serializer": json_serializer,
            "json_deserializer": json_deserializer,
            "json_default": json_default,
            "datefmt": datefmt,
            "use_datetime_directive": use_datetime_directive,
            "log_record_order": log_record_order,
            "utc": utc,
            "use_rfc3339": use_rfc3339,
        }

        self._init_logger(formatter_options=formatter_options, **kwargs)

    # Prevent __getattr__ from shielding unknown attribute errors in type checkers
    # https://github.com/awslabs/aws-lambda-powertools-python/issues/1660
    if not TYPE_CHECKING:

        def __getattr__(self, name):
            # Proxy attributes not found to actual logger to support backward compatibility
            # https://github.com/awslabs/aws-lambda-powertools-python/issues/97
            return getattr(self._logger, name)

    def _get_logger(self):
        """Returns a Logger named {self.service}, or {self.service.filename} for child loggers"""
        logger_name = self.service
        if self.child:
            logger_name = f"{self.service}.{self._get_caller_filename()}"

        return logging.getLogger(logger_name)

    def _init_logger(self, formatter_options: Optional[Dict] = None, **kwargs):
        """Configures new logger"""

        # Skip configuration if it's a child logger or a pre-configured logger
        # to prevent the following:
        #   a) multiple handlers being attached
        #   b) different sampling mechanisms
        #   c) multiple messages from being logged as handlers can be duplicated
        is_logger_preconfigured = getattr(self._logger, "init", False)
        if self.child or is_logger_preconfigured:
            return

        self._configure_sampling()
        self._logger.setLevel(self.log_level)
        self._logger.addHandler(self.logger_handler)
        self.structure_logs(formatter_options=formatter_options, **kwargs)

        # Maintenance: We can drop this upon Py3.7 EOL. It's a backport for "location" key to work
        self._logger.findCaller = self.findCaller

        # Pytest Live Log feature duplicates log records for colored output
        # but we explicitly add a filter for log deduplication.
        # This flag disables this protection when you explicit want logs to be duplicated (#262)
        if not self._is_deduplication_disabled:
            logger.debug("Adding filter in root logger to suppress child logger records to bubble up")
            for handler in logging.root.handlers:
                # It'll add a filter to suppress any child logger from self.service
                # Example: `Logger(service="order")`, where service is Order
                # It'll reject all loggers starting with `order` e.g. order.checkout, order.shared
                handler.addFilter(SuppressFilter(self.service))

        # as per bug in #249, we should not be pre-configuring an existing logger
        # therefore we set a custom attribute in the Logger that will be returned
        # std logging will return the same Logger with our attribute if name is reused
        logger.debug(f"Marking logger {self.service} as preconfigured")
        self._logger.init = True

    def _configure_sampling(self):
        """Dynamically set log level based on sampling rate

        Raises
        ------
        InvalidLoggerSamplingRateError
            When sampling rate provided is not a float
        """
        try:
            if self.sampling_rate and random.random() <= float(self.sampling_rate):
                logger.debug("Setting log level to Debug due to sampling rate")
                self.log_level = logging.DEBUG
        except ValueError:
            raise InvalidLoggerSamplingRateError(
                f"Expected a float value ranging 0 to 1, but received {self.sampling_rate} instead."
                f"Please review POWERTOOLS_LOGGER_SAMPLE_RATE environment variable."
            )

    def inject_lambda_context(
        self,
        lambda_handler: Optional[Callable[[Dict, Any], Any]] = None,
        log_event: Optional[bool] = None,
        correlation_id_path: Optional[str] = None,
        clear_state: Optional[bool] = False,
    ):
        """Decorator to capture Lambda contextual info and inject into logger

        Parameters
        ----------
        clear_state : bool, optional
            Instructs logger to remove any custom keys previously added
        lambda_handler : Callable
            Method to inject the lambda context
        log_event : bool, optional
            Instructs logger to log Lambda Event, by default False
        correlation_id_path: str, optional
            Optional JMESPath for the correlation_id

        Environment variables
        ---------------------
        POWERTOOLS_LOGGER_LOG_EVENT : str
            instruct logger to log Lambda Event (e.g. `"true", "True", "TRUE"`)

        Example
        -------
        **Captures Lambda contextual runtime info (e.g memory, arn, req_id)**

            from aws_lambda_powertools import Logger

            logger = Logger(service="payment")

            @logger.inject_lambda_context
            def handler(event, context):
                logger.info("Hello")

        **Captures Lambda contextual runtime info and logs incoming request**

            from aws_lambda_powertools import Logger

            logger = Logger(service="payment")

            @logger.inject_lambda_context(log_event=True)
            def handler(event, context):
                logger.info("Hello")

        Returns
        -------
        decorate : Callable
            Decorated lambda handler
        """

        # If handler is None we've been called with parameters
        # Return a partial function with args filled
        if lambda_handler is None:
            logger.debug("Decorator called with parameters")
            return functools.partial(
                self.inject_lambda_context,
                log_event=log_event,
                correlation_id_path=correlation_id_path,
                clear_state=clear_state,
            )

        log_event = resolve_truthy_env_var_choice(
            env=os.getenv(constants.LOGGER_LOG_EVENT_ENV, "false"), choice=log_event
        )

        @functools.wraps(lambda_handler)
        def decorate(event, context, *args, **kwargs):
            lambda_context = build_lambda_context_model(context)
            cold_start = _is_cold_start()

            if clear_state:
                self.structure_logs(cold_start=cold_start, **lambda_context.__dict__)
            else:
                self.append_keys(cold_start=cold_start, **lambda_context.__dict__)

            if correlation_id_path:
                self.set_correlation_id(jmespath.search(correlation_id_path, event))

            if log_event:
                logger.debug("Event received")
                self.info(getattr(event, "raw_event", event))

            return lambda_handler(event, context, *args, **kwargs)

        return decorate

    def info(
        self,
        msg: object,
        *args,
        exc_info=None,
        stack_info: bool = False,
        stacklevel: int = 2,
        extra: Optional[Mapping[str, object]] = None,
        **kwargs,
    ):
        extra = extra or {}
        extra = {**extra, **kwargs}

        # Maintenance: We can drop this upon Py3.7 EOL. It's a backport for "location" key to work
        if sys.version_info < (3, 8):  # pragma: no cover
            return self._logger.info(msg, *args, exc_info=exc_info, stack_info=stack_info, extra=extra)
        return self._logger.info(
            msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra
        )

    def error(
        self,
        msg: object,
        *args,
        exc_info=None,
        stack_info: bool = False,
        stacklevel: int = 2,
        extra: Optional[Mapping[str, object]] = None,
        **kwargs,
    ):
        extra = extra or {}
        extra = {**extra, **kwargs}

        # Maintenance: We can drop this upon Py3.7 EOL. It's a backport for "location" key to work
        if sys.version_info < (3, 8):  # pragma: no cover
            return self._logger.error(msg, *args, exc_info=exc_info, stack_info=stack_info, extra=extra)
        return self._logger.error(
            msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra
        )

    def exception(
        self,
        msg: object,
        *args,
        exc_info=True,
        stack_info: bool = False,
        stacklevel: int = 2,
        extra: Optional[Mapping[str, object]] = None,
        **kwargs,
    ):
        extra = extra or {}
        extra = {**extra, **kwargs}

        # Maintenance: We can drop this upon Py3.7 EOL. It's a backport for "location" key to work
        if sys.version_info < (3, 8):  # pragma: no cover
            return self._logger.exception(msg, *args, exc_info=exc_info, stack_info=stack_info, extra=extra)
        return self._logger.exception(
            msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra
        )

    def critical(
        self,
        msg: object,
        *args,
        exc_info=None,
        stack_info: bool = False,
        stacklevel: int = 2,
        extra: Optional[Mapping[str, object]] = None,
        **kwargs,
    ):
        extra = extra or {}
        extra = {**extra, **kwargs}

        # Maintenance: We can drop this upon Py3.7 EOL. It's a backport for "location" key to work
        if sys.version_info < (3, 8):  # pragma: no cover
            return self._logger.critical(msg, *args, exc_info=exc_info, stack_info=stack_info, extra=extra)
        return self._logger.critical(
            msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra
        )

    def warning(
        self,
        msg: object,
        *args,
        exc_info=None,
        stack_info: bool = False,
        stacklevel: int = 2,
        extra: Optional[Mapping[str, object]] = None,
        **kwargs,
    ):
        extra = extra or {}
        extra = {**extra, **kwargs}

        # Maintenance: We can drop this upon Py3.7 EOL. It's a backport for "location" key to work
        if sys.version_info < (3, 8):  # pragma: no cover
            return self._logger.warning(msg, *args, exc_info=exc_info, stack_info=stack_info, extra=extra)
        return self._logger.warning(
            msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra
        )

    def debug(
        self,
        msg: object,
        *args,
        exc_info=None,
        stack_info: bool = False,
        stacklevel: int = 2,
        extra: Optional[Mapping[str, object]] = None,
        **kwargs,
    ):
        extra = extra or {}
        extra = {**extra, **kwargs}

        # Maintenance: We can drop this upon Py3.7 EOL. It's a backport for "location" key to work
        if sys.version_info < (3, 8):  # pragma: no cover
            return self._logger.debug(msg, *args, exc_info=exc_info, stack_info=stack_info, extra=extra)
        return self._logger.debug(
            msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra
        )

    def append_keys(self, **additional_keys):
        self.registered_formatter.append_keys(**additional_keys)

    def remove_keys(self, keys: Iterable[str]):
        self.registered_formatter.remove_keys(keys)

    @property
    def registered_handler(self) -> logging.Handler:
        """Convenience property to access logger handler"""
        handlers = self._logger.parent.handlers if self.child else self._logger.handlers
        return handlers[0]

    @property
    def registered_formatter(self) -> BasePowertoolsFormatter:
        """Convenience property to access logger formatter"""
        return self.registered_handler.formatter  # type: ignore

    def structure_logs(self, append: bool = False, formatter_options: Optional[Dict] = None, **keys):
        """Sets logging formatting to JSON.

        Optionally, it can append keyword arguments
        to an existing logger, so it is available across future log statements.

        Last keyword argument and value wins if duplicated.

        Parameters
        ----------
        append : bool, optional
            append keys provided to logger formatter, by default False
        formatter_options : dict, optional
            LambdaPowertoolsFormatter options to be propagated, by default {}
        """
        formatter_options = formatter_options or {}

        # There are 3 operational modes for this method
        ## 1. Register a Powertools Formatter for the first time
        ## 2. Append new keys to the current logger formatter; deprecated in favour of append_keys
        ## 3. Add new keys and discard existing to the registered formatter

        # Mode 1
        log_keys = {**self._default_log_keys, **keys}
        is_logger_preconfigured = getattr(self._logger, "init", False)
        if not is_logger_preconfigured:
            formatter = self.logger_formatter or LambdaPowertoolsFormatter(**formatter_options, **log_keys)  # type: ignore # noqa: E501
            self.registered_handler.setFormatter(formatter)

            # when using a custom Lambda Powertools Formatter
            # standard and custom keys that are not Powertools Formatter parameters should be appended
            # and custom keys that might happen to be Powertools Formatter parameters should be discarded
            # this prevents adding them as custom keys, for example, `json_default=<callable>`
            # see https://github.com/awslabs/aws-lambda-powertools-python/issues/1263
            custom_keys = {k: v for k, v in log_keys.items() if k not in RESERVED_FORMATTER_CUSTOM_KEYS}
            return self.registered_formatter.append_keys(**custom_keys)

        # Mode 2 (legacy)
        if append:
            # Maintenance: Add deprecation warning for major version
            return self.append_keys(**keys)

        # Mode 3
        self.registered_formatter.clear_state()
        self.registered_formatter.append_keys(**log_keys)

    def set_correlation_id(self, value: Optional[str]):
        """Sets the correlation_id in the logging json

        Parameters
        ----------
        value : str, optional
            Value for the correlation id. None will remove the correlation_id
        """
        self.append_keys(correlation_id=value)

    def get_correlation_id(self) -> Optional[str]:
        """Gets the correlation_id in the logging json

        Returns
        -------
        str, optional
            Value for the correlation id
        """
        if isinstance(self.registered_formatter, LambdaPowertoolsFormatter):
            return self.registered_formatter.log_format.get("correlation_id")
        return None

    @staticmethod
    def _get_log_level(level: Union[str, int, None]) -> Union[str, int]:
        """Returns preferred log level set by the customer in upper case"""
        if isinstance(level, int):
            return level

        log_level: Optional[str] = level or os.getenv("LOG_LEVEL")
        if log_level is None:
            return logging.INFO

        return log_level.upper()

    @staticmethod
    def _get_caller_filename():
        """Return caller filename by finding the caller frame"""
        # Current frame         => _get_logger()
        # Previous frame        => logger.py
        # Before previous frame => Caller
        frame = inspect.currentframe()
        caller_frame = frame.f_back.f_back.f_back
        return caller_frame.f_globals["__name__"]

    # Maintenance: We can drop this upon Py3.7 EOL. It's a backport for "location" key to work
    def findCaller(self, stack_info=False, stacklevel=2):  # pragma: no cover
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = logging.currentframe()  # noqa: VNE001
        # On some versions of IronPython, currentframe() returns None if
        # IronPython isn't run with -X:Frames.
        if f is None:
            return "(unknown file)", 0, "(unknown function)", None
        while stacklevel > 0:
            next_f = f.f_back
            if next_f is None:
                ## We've got options here.
                ## If we want to use the last (deepest) frame:
                break
                ## If we want to mimic the warnings module:
                # return ("sys", 1, "(unknown function)", None) # noqa: E800
                ## If we want to be pedantic:  # noqa: E800
                # raise ValueError("call stack is not deep enough") # noqa: E800
            f = next_f  # noqa: VNE001
            if not _is_internal_frame(f):
                stacklevel -= 1
        co = f.f_code
        sinfo = None
        if stack_info:
            with io.StringIO() as sio:
                sio.write("Stack (most recent call last):\n")
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == "\n":
                    sinfo = sinfo[:-1]
        return co.co_filename, f.f_lineno, co.co_name, sinfo


def set_package_logger(
    level: Union[str, int] = logging.DEBUG,
    stream: Optional[IO[str]] = None,
    formatter: Optional[logging.Formatter] = None,
):
    """Set an additional stream handler, formatter, and log level for aws_lambda_powertools package logger.

    **Package log by default is suppressed (NullHandler), this should only used for debugging.
    This is separate from application Logger class utility**

    Example
    -------
    **Enables debug logging for AWS Lambda Powertools package**

        >>> aws_lambda_powertools.logging.logger import set_package_logger
        >>> set_package_logger()

    Parameters
    ----------
    level: str, int
        log level, DEBUG by default
    stream: sys.stdout
        log stream, stdout by default
    formatter: logging.Formatter
        log formatter, "%(asctime)s %(name)s [%(levelname)s] %(message)s" by default
    """
    if formatter is None:
        formatter = logging.Formatter("%(asctime)s %(name)s [%(levelname)s] %(message)s")

    if stream is None:
        stream = sys.stdout

    logger = logging.getLogger("aws_lambda_powertools")
    logger.setLevel(level)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# Maintenance: We can drop this upon Py3.7 EOL. It's a backport for "location" key to work
# The following is based on warnings._is_internal_frame. It makes sure that
# frames of the import mechanism are skipped when logging at module level and
# using a stacklevel value greater than one.
def _is_internal_frame(frame):  # pragma: no cover
    """Signal whether the frame is a CPython or logging module internal."""
    filename = os.path.normcase(frame.f_code.co_filename)
    return filename == logging._srcfile or ("importlib" in filename and "_bootstrap" in filename)
