import copy
import functools
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


class Logger(logging.Logger):
    """Creates and setups a logger to format statements in JSON.

    Includes service name and any additional key=value into logs
    It also accepts both service name or level explicitly via env vars

    Environment variables
    ---------------------
    POWERTOOLS_SERVICE_NAME : str
        service name
    LOG_LEVEL: str, int
        logging level (e.g. INFO, DEBUG)
    POWERTOOLS_LOGGER_SAMPLE_RATE: float
        samping rate ranging from 0 to 1, 1 being 100% sampling

    Parameters
    ----------
    service : str, optional
        service name to be appended in logs, by default "service_undefined"
    level : str, optional
        logging.level, by default "INFO"
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

    **Append payment_id to previously setup structured log logger**

        >>> from aws_lambda_powertools import Logger
        >>> logger = Logger(service="payment")
        >>>
        >>> def handler(event, context):
                logger.structure_logs(append=True, payment_id=event["payment_id"])
                logger.info("Hello")

    Parameters
    ----------
    logging : logging.Logger
        Inherits Logger
    service: str
        name of the service to create the logger for, "service_undefined" by default
    level: str, int
        log level, INFO by default
    sampling_rate: float
        debug log sampling rate, 0.0 by default
    stream: sys.stdout
        log stream, stdout by default

    Raises
    ------
    InvalidLoggerSamplingRateError
        When sampling rate provided is not a float
    """

    def __init__(
        self,
        service: str = None,
        level: Union[str, int] = None,
        sampling_rate: float = None,
        stream: sys.stdout = None,
        **kwargs,
    ):
        self.service = service or os.getenv("POWERTOOLS_SERVICE_NAME") or "service_undefined"
        self.sampling_rate = sampling_rate or os.getenv("POWERTOOLS_LOGGER_SAMPLE_RATE") or 0.0
        self.log_level = level or os.getenv("LOG_LEVEL") or logging.INFO
        self.handler = logging.StreamHandler(stream) if stream is not None else logging.StreamHandler(sys.stdout)
        self._default_log_keys = {"service": self.service, "sampling_rate": self.sampling_rate}
        self.log_keys = copy.copy(self._default_log_keys)

        super().__init__(name=self.service, level=self.log_level)

        try:
            if self.sampling_rate and random.random() <= float(self.sampling_rate):
                logger.debug("Setting log level to Debug due to sampling rate")
                self.log_level = logging.DEBUG
        except ValueError:
            raise InvalidLoggerSamplingRateError(
                f"Expected a float value ranging 0 to 1, but received {self.sampling_rate} instead. Please review POWERTOOLS_LOGGER_SAMPLE_RATE environment variable."  # noqa E501
            )

        self.setLevel(self.log_level)
        self.structure_logs(**kwargs)
        self.addHandler(self.handler)

    def inject_lambda_context(self, lambda_handler: Callable[[Dict, Any], Any] = None, log_event: bool = False):
        """Decorator to capture Lambda contextual info and inject into struct logging

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

            self.structure_logs(cold_start=cold_start, **lambda_context.__dict__)
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
        self.handler.setFormatter(JsonFormatter(**self._default_log_keys, **kwargs))

        if append:
            new_keys = {**self.log_keys, **kwargs}
            self.handler.setFormatter(JsonFormatter(**new_keys))

        self.log_keys.update(**kwargs)


def set_package_logger(
    level: Union[str, int] = logging.DEBUG, stream: sys.stdout = None, formatter: logging.Formatter = None
):
    """Set an additional stream handler, formatter, and log level for aws_lambda_powertools package logger.

    **Package log by default is supressed (NullHandler), this should only used for debugging.
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
