import functools
import inspect
import logging
import os
import random
import sys
from distutils.util import strtobool
from typing import Any, Callable, Dict, Union

from .exceptions import InvalidLoggerSamplingRateError
from .formatter import JsonFormatter
from .lambda_context import build_lambda_context_model

logger = logging.getLogger(__name__)

is_cold_start = True


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
        samping rate ranging from 0 to 1, 1 being 100% sampling

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
                logger.structure_logs(append=True, payment_id=event["payment_id"])
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

    Raises
    ------
    InvalidLoggerSamplingRateError
        When sampling rate provided is not a float
    """

    def __init__(
        self,
        service: str = None,
        level: Union[str, int] = None,
        child: bool = False,
        sampling_rate: float = None,
        stream: sys.stdout = None,
        **kwargs,
    ):
        self.service = service or os.getenv("POWERTOOLS_SERVICE_NAME") or "service_undefined"
        self.sampling_rate = sampling_rate or os.getenv("POWERTOOLS_LOGGER_SAMPLE_RATE") or 0.0
        self.log_level = self._get_log_level(level)
        self.child = child
        self._handler = logging.StreamHandler(stream) if stream is not None else logging.StreamHandler(sys.stdout)
        self._default_log_keys = {"service": self.service, "sampling_rate": self.sampling_rate}
        self._logger = self._get_logger()

        self._init_logger(**kwargs)

    def __getattr__(self, name):
        # Proxy attributes not found to actual logger to support backward compatibility
        # https://github.com/awslabs/aws-lambda-powertools-python/issues/97
        return getattr(self._logger, name)

    def _get_log_level(self, level: Union[str, int]) -> Union[str, int]:
        """ Returns preferred log level set by the customer in upper case """
        if isinstance(level, int):
            return level

        log_level: str = level or os.getenv("LOG_LEVEL")
        log_level = log_level.upper() if log_level is not None else logging.INFO

        return log_level

    def _get_logger(self):
        """ Returns a Logger named {self.service}, or {self.service.filename} for child loggers"""
        logger_name = self.service
        if self.child:
            logger_name = f"{self.service}.{self._get_caller_filename()}"

        return logging.getLogger(logger_name)

    def _get_caller_filename(self):
        """ Return caller filename by finding the caller frame """
        # Current frame         => _get_logger()
        # Previous frame        => logger.py
        # Before previous frame => Caller
        frame = inspect.currentframe()
        caller_frame = frame.f_back.f_back.f_back
        filename = caller_frame.f_globals["__name__"]

        return filename

    def _init_logger(self, **kwargs):
        """Configures new logger"""

        # Lambda by default configures the root logger handler
        # therefore, we need to remove it to prevent messages being logged twice
        # when customers use our Logger
        logger.debug("Removing Lambda root handler whether it exists")
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Skip configuration if it's a child logger to prevent
        # multiple handlers being attached as well as different sampling mechanisms
        # and multiple messages from being logged as handlers can be duplicated
        if not self.child:
            self._configure_sampling()
            self._logger.setLevel(self.log_level)
            self._logger.addHandler(self._handler)
            self.structure_logs(**kwargs)

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

    def inject_lambda_context(self, lambda_handler: Callable[[Dict, Any], Any] = None, log_event: bool = False):
        """Decorator to capture Lambda contextual info and inject into logger

        Parameters
        ----------
        log_event : bool, optional
            Instructs logger to log Lambda Event, by default False

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
            return functools.partial(self.inject_lambda_context, log_event=log_event)

        log_event_env_option = str(os.getenv("POWERTOOLS_LOGGER_LOG_EVENT", "false"))
        log_event = strtobool(log_event_env_option) or log_event

        @functools.wraps(lambda_handler)
        def decorate(event, context):
            if log_event:
                logger.debug("Event received")
                self.info(event)

            lambda_context = build_lambda_context_model(context)
            cold_start = _is_cold_start()

            self.structure_logs(append=True, cold_start=cold_start, **lambda_context.__dict__)
            return lambda_handler(event, context)

        return decorate

    def structure_logs(self, append: bool = False, **kwargs):
        """Sets logging formatting to JSON.

        Optionally, it can append keyword arguments
        to an existing logger so it is available
        across future log statements.

        Last keyword argument and value wins if duplicated.

        Parameters
        ----------
        append : bool, optional
            [description], by default False
        """

        # Child loggers don't have handlers attached, use its parent handlers
        handlers = self._logger.parent.handlers if self.child else self._logger.handlers
        for handler in handlers:
            if append:
                # Update existing formatter in an existing logger handler
                handler.formatter.update_formatter(**kwargs)
            else:
                # Set a new formatter for a logger handler
                handler.setFormatter(JsonFormatter(**self._default_log_keys, **kwargs))


def set_package_logger(
    level: Union[str, int] = logging.DEBUG, stream: sys.stdout = None, formatter: logging.Formatter = None
):
    """Set an additional stream handler, formatter, and log level for aws_lambda_powertools package logger.

    **Package log by default is suppressed (NullHandler), this should only used for debugging.
    This is separate from application Logger class utility**

    Example
    -------
    **Enables debug logging for AWS Lambda Powertools package**

        >>> from aws_lambda_powertools.logging.logger import set_package_logger
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
