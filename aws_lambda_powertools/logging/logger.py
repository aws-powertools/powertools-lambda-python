"""
Logger utility
!!! abstract "Usage Documentation"
    [`Logger`](../../core/logger.md)
"""

from __future__ import annotations

import functools
import inspect
import logging
import os
import random
import sys
import warnings
from contextlib import contextmanager
from typing import IO, TYPE_CHECKING, Any, TypeVar, cast, overload

from aws_lambda_powertools.logging.buffer.cache import LoggerBufferCache
from aws_lambda_powertools.logging.buffer.functions import _check_minimum_buffer_log_level, _create_buffer_record
from aws_lambda_powertools.logging.constants import (
    LOGGER_ATTRIBUTE_HANDLER,
    LOGGER_ATTRIBUTE_POWERTOOLS_HANDLER,
    LOGGER_ATTRIBUTE_PRECONFIGURED,
)
from aws_lambda_powertools.logging.exceptions import (
    InvalidLoggerSamplingRateError,
    OrphanedChildLoggerError,
)
from aws_lambda_powertools.logging.filters import SuppressFilter
from aws_lambda_powertools.logging.formatter import (
    RESERVED_FORMATTER_CUSTOM_KEYS,
    BasePowertoolsFormatter,
    LambdaPowertoolsFormatter,
)
from aws_lambda_powertools.logging.lambda_context import build_lambda_context_model
from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import (
    extract_event_from_common_models,
    get_tracer_id,
    resolve_env_var_choice,
    resolve_truthy_env_var_choice,
)
from aws_lambda_powertools.utilities import jmespath_utils
from aws_lambda_powertools.warnings import PowertoolsUserWarning

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable, Mapping

    from aws_lambda_powertools.logging.buffer.config import LoggerBufferConfig
    from aws_lambda_powertools.shared.types import AnyCallableT


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
    global is_cold_start

    initialization_type = os.getenv(constants.LAMBDA_INITIALIZATION_TYPE)

    # Check for Provisioned Concurrency environment
    # AWS_LAMBDA_INITIALIZATION_TYPE is set when using Provisioned Concurrency
    if initialization_type == "provisioned-concurrency":
        is_cold_start = False
        return False

    if not is_cold_start:
        return False

    # This is a cold start - flip the flag and return True
    is_cold_start = False
    return True


class Logger:
    """Creates and setups a logger to format statements in JSON.

    Includes service name and any additional key=value into logs
    It also accepts both service name or level explicitly via env vars

    Environment variables
    ---------------------
    POWERTOOLS_SERVICE_NAME : str
        service name
    POWERTOOLS_LOG_LEVEL: str
        logging level (e.g. INFO, DEBUG)
    POWERTOOLS_LOGGER_SAMPLE_RATE: float
        sampling rate ranging from 0 to 1, 1 being 100% sampling

    Parameters
    ----------
    service : str, optional
        service name to be appended in logs, by default "service_undefined"
    level : str, int optional
        The level to set. Can be a string representing the level name: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        or an integer representing the level value: 10 for 'DEBUG', 20 for 'INFO', 30 for 'WARNING', 40 for 'ERROR', 50 for 'CRITICAL'.
        by default "INFO"
    child: bool, optional
        create a child Logger named <service>.<caller_file_name>, False by default
    sampling_rate: float, optional
        sample rate for debug calls within execution context defaults to 0.0
    stream: sys.stdout, optional
        valid output for a logging stream, by default sys.stdout
    logger_formatter: PowertoolsFormatter, optional
        custom logging formatter that implements PowertoolsFormatter
    logger_handler: logging.Handler, optional
        custom logging handler e.g. logging.FileHandler("file.log")
    log_uncaught_exceptions: bool, by default False
        logs uncaught exception using sys.excepthook
    buffer_config: LoggerBufferConfig, optional
        logger buffer configuration

        See: https://docs.python.org/3/library/sys.html#sys.excepthook


    Parameters propagated to LambdaPowertoolsFormatter
    --------------------------------------------------
    datefmt: str, optional
        String directives (strftime) to format log timestamp using `time`, by default it uses 2021-05-03 11:47:12,494+0200.
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
    """  # noqa: E501

    def __init__(
        self,
        service: str | None = None,
        level: str | int | None = None,
        child: bool = False,
        sampling_rate: float | None = None,
        stream: IO[str] | None = None,
        logger_formatter: PowertoolsFormatter | None = None,
        logger_handler: logging.Handler | None = None,
        log_uncaught_exceptions: bool = False,
        json_serializer: Callable[[dict], str] | None = None,
        json_deserializer: Callable[[dict | str | bool | int | float], str] | None = None,
        json_default: Callable[[Any], Any] | None = None,
        datefmt: str | None = None,
        use_datetime_directive: bool = False,
        log_record_order: list[str] | None = None,
        utc: bool = False,
        use_rfc3339: bool = False,
        serialize_stacktrace: bool = True,
        buffer_config: LoggerBufferConfig | None = None,
        **kwargs,
    ) -> None:
        self.service = resolve_env_var_choice(
            choice=service,
            env=os.getenv(constants.SERVICE_NAME_ENV, "service_undefined"),
        )
        self.sampling_rate = resolve_env_var_choice(
            choice=sampling_rate,
            env=os.getenv(constants.LOGGER_LOG_SAMPLING_RATE),
        )
        self._default_log_keys: dict[str, Any] = {"service": self.service, "sampling_rate": self.sampling_rate}
        self.child = child
        self.logger_formatter = logger_formatter
        self._stream = stream or sys.stdout

        self.log_uncaught_exceptions = log_uncaught_exceptions

        self._is_deduplication_disabled = resolve_truthy_env_var_choice(
            env=os.getenv(constants.LOGGER_LOG_DEDUPLICATION_ENV, "false"),
        )
        self._logger = self._get_logger()
        self.logger_handler = logger_handler or self._get_handler()

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
            "serialize_stacktrace": serialize_stacktrace,
        }

        self._buffer_config = buffer_config
        if self._buffer_config:
            self._buffer_cache = LoggerBufferCache(max_size_bytes=self._buffer_config.max_bytes)

        # Used in case of sampling
        self.initial_log_level = self._determine_log_level(level)

        self._init_logger(
            formatter_options=formatter_options,
            log_level=level,
            buffer_config=self._buffer_config,
            buffer_cache=getattr(self, "_buffer_cache", None),
            **kwargs,
        )

        if self.log_uncaught_exceptions:
            logger.debug("Replacing exception hook")
            sys.excepthook = functools.partial(log_uncaught_exception_hook, logger=self)

    # Prevent __getattr__ from shielding unknown attribute errors in type checkers
    # https://github.com/aws-powertools/powertools-lambda-python/issues/1660
    if not TYPE_CHECKING:  # pragma: no cover

        def __getattr__(self, name):
            # Proxy attributes not found to actual logger to support backward compatibility
            # https://github.com/aws-powertools/powertools-lambda-python/issues/97
            return getattr(self._logger, name)

    def _get_logger(self) -> logging.Logger:
        """Returns a Logger named {self.service}, or {self.service.filename} for child loggers"""
        logger_name = self.service
        if self.child:
            logger_name = f"{self.service}.{_get_caller_filename()}"

        return logging.getLogger(logger_name)

    def _get_handler(self) -> logging.Handler:
        # is a logger handler already configured?
        if getattr(self, LOGGER_ATTRIBUTE_HANDLER, None):
            return self.logger_handler

        # Detect Powertools logger by checking for unique handler
        # Retrieve the first handler if it's a Powertools instance
        if getattr(self._logger, "powertools_handler", None):
            return self._logger.handlers[0]

        # for children, use parent's handler
        if self.child:
            return getattr(self._logger.parent, LOGGER_ATTRIBUTE_POWERTOOLS_HANDLER, None)  # type: ignore[return-value] # always checked in formatting

        # otherwise, create a new stream handler (first time init)
        return logging.StreamHandler(self._stream)

    def _init_logger(
        self,
        formatter_options: dict | None = None,
        log_level: str | int | None = None,
        buffer_config: LoggerBufferConfig | None = None,
        buffer_cache: LoggerBufferCache | None = None,
        **kwargs,
    ) -> None:
        """Configures new logger"""

        # Skip configuration if it's a child logger or a pre-configured logger
        # to prevent the following:
        #   a) multiple handlers being attached
        #   b) different sampling mechanisms
        #   c) multiple messages from being logged as handlers can be duplicated
        is_logger_preconfigured = getattr(self._logger, LOGGER_ATTRIBUTE_PRECONFIGURED, False)
        if self.child:
            self.setLevel(log_level)
            if getattr(self._logger.parent, "powertools_buffer_config", None):
                # Initializes a new, empty LoggerBufferCache for child logger
                # Preserves parent's buffer configuration while resetting cache contents
                self._buffer_config = self._logger.parent.powertools_buffer_config  # type: ignore[union-attr]
                self._buffer_cache = LoggerBufferCache(self._logger.parent.powertools_buffer_config.max_bytes)  # type: ignore[union-attr]
            return

        if is_logger_preconfigured:
            # Reuse existing buffer configuration from a previously configured logger
            # Ensures consistent buffer settings across logger instances within the same service
            # Enables buffer propagation and maintains a unified logging configuration
            self._buffer_config = self._logger.powertools_buffer_config  # type: ignore[attr-defined]
            self._buffer_cache = self._logger.powertools_buffer_cache  # type: ignore[attr-defined]
            return

        self.setLevel(log_level)
        self._configure_sampling()
        self.addHandler(self.logger_handler)
        self.structure_logs(formatter_options=formatter_options, **kwargs)

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
        self._logger.init = True  # type: ignore[attr-defined]
        self._logger.powertools_handler = self.logger_handler  # type: ignore[attr-defined]
        self._logger.powertools_buffer_config = buffer_config  # type: ignore[attr-defined]
        self._logger.powertools_buffer_cache = buffer_cache  # type: ignore[attr-defined]

    def refresh_sample_rate_calculation(self) -> None:
        """
        Refreshes the sample rate calculation by reconfiguring logging settings.

        Returns
        -------
            None
        """
        self._logger.setLevel(self.initial_log_level)
        self._configure_sampling()

    def _configure_sampling(self) -> None:
        """Dynamically set log level based on sampling rate

        Raises
        ------
        InvalidLoggerSamplingRateError
            When sampling rate provided is not a float
        """
        if not self.sampling_rate:
            return

        try:
            # This is not testing < 0 or > 1 conditions
            # Because I don't need other if condition here
            if random.random() <= float(self.sampling_rate):
                self._logger.setLevel(logging.DEBUG)
                logger.debug("Setting log level to DEBUG due to sampling rate")
        except ValueError:
            raise InvalidLoggerSamplingRateError(
                (
                    f"Expected a float value ranging 0 to 1, but received {self.sampling_rate} instead."
                    "Please review POWERTOOLS_LOGGER_SAMPLE_RATE environment variable or `sampling_rate` parameter."
                ),
            )

    @overload
    def inject_lambda_context(
        self,
        lambda_handler: AnyCallableT,
        log_event: bool | None = None,
        correlation_id_path: str | None = None,
        clear_state: bool | None = False,
        flush_buffer_on_uncaught_error: bool = False,
    ) -> AnyCallableT: ...

    @overload
    def inject_lambda_context(
        self,
        lambda_handler: None = None,
        log_event: bool | None = None,
        correlation_id_path: str | None = None,
        clear_state: bool | None = False,
        flush_buffer_on_uncaught_error: bool = False,
    ) -> Callable[[AnyCallableT], AnyCallableT]: ...

    def inject_lambda_context(
        self,
        lambda_handler: AnyCallableT | None = None,
        log_event: bool | None = None,
        correlation_id_path: str | None = None,
        clear_state: bool | None = False,
        flush_buffer_on_uncaught_error: bool = False,
    ) -> Any:
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
                flush_buffer_on_uncaught_error=flush_buffer_on_uncaught_error,
            )

        log_event = resolve_truthy_env_var_choice(
            env=os.getenv(constants.LOGGER_LOG_EVENT_ENV, "false"),
            choice=log_event,
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
                self.set_correlation_id(
                    jmespath_utils.query(envelope=correlation_id_path, data=event),
                )

            if log_event:
                logger.debug("Event received")
                self.info(extract_event_from_common_models(event))

            # Sampling rate is defined, and this is not ColdStart
            # then we need to recalculate the sampling
            # See: https://github.com/aws-powertools/powertools-lambda-python/issues/6141
            if self.sampling_rate and not cold_start:
                self.refresh_sample_rate_calculation()

            try:
                # Execute the Lambda handler with provided event and context
                return lambda_handler(event, context, *args, **kwargs)
            except:
                # Flush the log buffer if configured to do so on uncaught errors
                # Ensures logging state is cleaned up even if an exception is raised
                if flush_buffer_on_uncaught_error:
                    logger.debug("Uncaught error detected, flushing log buffer before exit")
                    self.flush_buffer()
                # Re-raise any exceptions that occur during handler execution
                raise
            finally:
                # Clear the cache after invocation is complete
                if self._buffer_config:
                    self._buffer_cache.clear()

        return decorate

    def debug(
        self,
        msg: object,
        *args: object,
        exc_info: logging._ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 2,
        extra: Mapping[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        extra = extra or {}
        extra = {**extra, **kwargs}

        # Logging workflow for logging.debug:
        # 1. Buffer is completely disabled - log right away
        # 2. DEBUG is the maximum level of buffer, so, can't bypass if enabled
        # 3. Store in buffer for potential later processing

        # MAINTAINABILITY_DECISION:
        # Keeping this implementation to avoid complex code handling.
        # Also for clarity over complexity

        # Buffer is not active and we need to log immediately
        if not self._buffer_config:
            return self._logger.debug(
                msg,
                *args,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra,
            )

        # Store record in the buffer
        self._add_log_record_to_buffer(
            level=logging.DEBUG,
            msg=msg,
            args=args,
            exc_info=exc_info,
            stack_info=stack_info,
            extra=extra,
        )

    def info(
        self,
        msg: object,
        *args: object,
        exc_info: logging._ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 2,
        extra: Mapping[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        extra = extra or {}
        extra = {**extra, **kwargs}

        # Logging workflow for logging.info:
        # 1. Buffer is completely disabled - log right away
        # 2. Log severity exceeds buffer's minimum threshold - bypass buffering
        # 3. If neither condition met, store in buffer for potential later processing

        # MAINTAINABILITY_DECISION:
        # Keeping this implementation to avoid complex code handling.
        # Also for clarity over complexity

        # Buffer is not active and we need to log immediately
        if not self._buffer_config:
            return self._logger.info(
                msg,
                *args,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra,
            )

        # Bypass buffer when log severity meets or exceeds configured minimum
        if _check_minimum_buffer_log_level(self._buffer_config.buffer_at_verbosity, "INFO"):
            return self._logger.info(
                msg,
                *args,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra,
            )

        # Store record in the buffer
        self._add_log_record_to_buffer(
            level=logging.INFO,
            msg=msg,
            args=args,
            exc_info=exc_info,
            stack_info=stack_info,
            extra=extra,
        )

    def warning(
        self,
        msg: object,
        *args: object,
        exc_info: logging._ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 2,
        extra: Mapping[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        extra = extra or {}
        extra = {**extra, **kwargs}

        # Logging workflow for logging.warning:
        # 1. Buffer is completely disabled - log right away
        # 2. Log severity exceeds buffer's minimum threshold - bypass buffering
        # 3. If neither condition met, store in buffer for potential later processing

        # MAINTAINABILITY_DECISION:
        # Keeping this implementation to avoid complex code handling.
        # Also for clarity over complexity

        # Buffer is not active and we need to log immediately
        if not self._buffer_config:
            return self._logger.warning(
                msg,
                *args,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra,
            )

        # Bypass buffer when log severity meets or exceeds configured minimum
        if _check_minimum_buffer_log_level(self._buffer_config.buffer_at_verbosity, "WARNING"):
            return self._logger.warning(
                msg,
                *args,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra,
            )

        # Store record in the buffer
        self._add_log_record_to_buffer(
            level=logging.WARNING,
            msg=msg,
            args=args,
            exc_info=exc_info,
            stack_info=stack_info,
            extra=extra,
        )

    def error(
        self,
        msg: object,
        *args: object,
        exc_info: logging._ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 2,
        extra: Mapping[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        extra = extra or {}
        extra = {**extra, **kwargs}

        # Workflow: Error Logging with automatic buffer flushing
        # 1. Buffer configuration checked for immediate flush
        # 2. If auto-flush enabled, trigger complete buffer processing
        # 3. Error log is not "bufferable", so ensure error log is immediately available

        if self._buffer_config and self._buffer_config.flush_on_error_log:
            self.flush_buffer()

        return self._logger.error(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
        )

    def critical(
        self,
        msg: object,
        *args: object,
        exc_info: logging._ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 2,
        extra: Mapping[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        extra = extra or {}
        extra = {**extra, **kwargs}

        # Workflow: Error Logging with automatic buffer flushing
        # 1. Buffer configuration checked for immediate flush
        # 2. If auto-flush enabled, trigger complete buffer processing
        # 3. Critical log is not "bufferable", so ensure error log is immediately available

        if self._buffer_config and self._buffer_config.flush_on_error_log:
            self.flush_buffer()

        return self._logger.critical(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
        )

    def exception(
        self,
        msg: object,
        *args: object,
        exc_info: logging._ExcInfoType = True,
        stack_info: bool = False,
        stacklevel: int = 2,
        extra: Mapping[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        extra = extra or {}
        extra = {**extra, **kwargs}

        # Workflow: Error Logging with automatic buffer flushing
        # 1. Buffer configuration checked for immediate flush
        # 2. If auto-flush enabled, trigger complete buffer processing
        # 3. Exception log is not "bufferable", so ensure error log is immediately available
        if self._buffer_config and self._buffer_config.flush_on_error_log:
            self.flush_buffer()

        return self._logger.exception(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
        )

    def append_keys(self, **additional_keys: object) -> None:
        self.registered_formatter.append_keys(**additional_keys)

    def get_current_keys(self) -> dict[str, Any]:
        return self.registered_formatter.get_current_keys()

    def remove_keys(self, keys: Iterable[str]) -> None:
        self.registered_formatter.remove_keys(keys)

    @contextmanager
    def append_context_keys(self, **additional_keys: Any) -> Generator[None, None, None]:
        """
        Context manager to temporarily add logging keys.

        Parameters
        -----------
        **additional_keys: Any
            Key-value pairs to include in the log context during the lifespan of the context manager.

        Example
        --------
        **Logging with contextual keys**

            logger = Logger(service="example_service")
            with logger.append_context_keys(user_id="123", operation="process"):
                logger.info("Log with context")
            logger.info("Log without context")
        """
        with self.registered_formatter.append_context_keys(**additional_keys):
            yield

    def clear_state(self) -> None:
        """Removes all custom keys that were appended to the Logger."""
        # Clear all custom keys from the formatter
        self.registered_formatter.clear_state()

        # Reset to default keys
        self.structure_logs(**self._default_log_keys)

    # These specific thread-safe methods are necessary to manage shared context in concurrent environments.
    # They prevent race conditions and ensure data consistency across multiple threads.
    def thread_safe_append_keys(self, **additional_keys: object) -> None:
        # Append additional key-value pairs to the context safely in a thread-safe manner.
        self.registered_formatter.thread_safe_append_keys(**additional_keys)

    def thread_safe_get_current_keys(self) -> dict[str, Any]:
        # Retrieve the current context keys safely in a thread-safe manner.
        return self.registered_formatter.thread_safe_get_current_keys()

    def thread_safe_remove_keys(self, keys: Iterable[str]) -> None:
        # Remove specified keys from the context safely in a thread-safe manner.
        self.registered_formatter.thread_safe_remove_keys(keys)

    def thread_safe_clear_keys(self) -> None:
        # Clear all keys from the context safely in a thread-safe manner.
        self.registered_formatter.thread_safe_clear_keys()

    def structure_logs(self, append: bool = False, formatter_options: dict | None = None, **keys) -> None:
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
        ## 1. Register a Powertools for AWS Lambda (Python) Formatter for the first time
        ## 2. Append new keys to the current logger formatter; deprecated in favour of append_keys
        ## 3. Add new keys and discard existing to the registered formatter

        # Mode 1
        log_keys = {**self._default_log_keys, **keys}
        is_logger_preconfigured = getattr(self._logger, LOGGER_ATTRIBUTE_PRECONFIGURED, False)
        if not is_logger_preconfigured:
            formatter = self.logger_formatter or LambdaPowertoolsFormatter(**formatter_options, **log_keys)
            self.registered_handler.setFormatter(formatter)

            # when using a custom Powertools for AWS Lambda (Python) Formatter
            # standard and custom keys that are not Powertools for AWS Lambda (Python) Formatter parameters
            # should be appended and custom keys that might happen to be Powertools for AWS Lambda (Python)
            # Formatter parameters should be discarded this prevents adding them as custom keys, for example,
            # `json_default=<callable>` see https://github.com/aws-powertools/powertools-lambda-python/issues/1263
            custom_keys = {k: v for k, v in log_keys.items() if k not in RESERVED_FORMATTER_CUSTOM_KEYS}
            return self.registered_formatter.append_keys(**custom_keys)

        # Mode 2 (legacy)
        if append:
            # Maintenance: Add deprecation warning for major version
            return self.append_keys(**keys)

        # Mode 3
        self.registered_formatter.clear_state()
        self.registered_formatter.thread_safe_clear_keys()
        self.registered_formatter.append_keys(**log_keys)

    def set_correlation_id(self, value: str | None) -> None:
        """Sets the correlation_id in the logging json

        Parameters
        ----------
        value : str, optional
            Value for the correlation id. None will remove the correlation_id
        """
        self.append_keys(correlation_id=value)

    def get_correlation_id(self) -> str | None:
        """Gets the correlation_id in the logging json

        Returns
        -------
        str, optional
            Value for the correlation id
        """
        if isinstance(self.registered_formatter, LambdaPowertoolsFormatter):
            return self.registered_formatter.log_format.get("correlation_id")
        return None

    def setLevel(self, level: str | int | None) -> None:
        return self._logger.setLevel(self._determine_log_level(level))

    def addHandler(self, handler: logging.Handler) -> None:
        return self._logger.addHandler(handler)

    def addFilter(self, filter: logging._FilterType) -> None:  # noqa: A002 # filter built-in usage
        return self._logger.addFilter(filter)

    def removeFilter(self, filter: logging._FilterType) -> None:  # noqa: A002 # filter built-in usage
        return self._logger.removeFilter(filter)

    @property
    def registered_handler(self) -> logging.Handler:
        """Convenience property to access the first logger handler"""
        # We ignore mypy here because self.child encodes whether or not self._logger.parent is
        # None, mypy can't see this from context but we can
        return self._get_handler()

    @property
    def registered_formatter(self) -> BasePowertoolsFormatter:
        """Convenience property to access the first logger formatter"""
        handler = self.registered_handler
        if handler is None:
            raise OrphanedChildLoggerError(
                "Orphan child loggers cannot append nor remove keys until a parent is initialized first. "
                "To solve this issue, you can A) make sure a parent logger is initialized first, or B) move append/remove keys operations to a later stage."  # noqa: E501
                "Reference: https://docs.powertools.aws.dev/lambda/python/latest/core/logger/#reusing-logger-across-your-code",
            )

        return cast(BasePowertoolsFormatter, handler.formatter)

    @property
    def log_level(self) -> int:
        return self._logger.level

    @property
    def name(self) -> str:
        return self._logger.name

    @property
    def handlers(self) -> list[logging.Handler]:
        """List of registered logging handlers

        Notes
        -----

        Looking for the first configured handler? Use registered_handler property instead.
        """
        return self._logger.handlers

    def _get_aws_lambda_log_level(self) -> str | None:
        """
        Retrieve the log level for AWS Lambda from the Advanced Logging Controls feature.
        Returns:
            str | None: The corresponding logging level.
        """

        return constants.LAMBDA_ADVANCED_LOGGING_LEVELS.get(os.getenv(constants.LAMBDA_LOG_LEVEL_ENV))

    def _get_powertools_log_level(self, level: str | int | None) -> str | None:
        """Retrieve the log level for Powertools from the environment variable or level parameter.
        If log level is an integer, we convert to its respective string level `logging.getLevelName()`.
        If no log level is provided, we check env vars for the log level: POWERTOOLS_LOG_LEVEL_ENV and POWERTOOLS_LOG_LEVEL_LEGACY_ENV.
        Parameters:
        -----------
        level : str | int | None
            The specified log level as a string, integer, or None.
        Environment variables
        ---------------------
        POWERTOOLS_LOG_LEVEL : str
            log level (e.g: INFO, DEBUG, WARNING, ERROR, CRITICAL)
        LOG_LEVEL (Legacy) : str
            log level (e.g: INFO, DEBUG, WARNING, ERROR, CRITICAL)
        Returns:
        --------
        str | None:
            The corresponding logging level. Returns None if the log level is not explicitly specified.
        """  # noqa E501

        # Extract log level from Powertools Logger env vars
        log_level_env = os.getenv(constants.POWERTOOLS_LOG_LEVEL_ENV) or os.getenv(
            constants.POWERTOOLS_LOG_LEVEL_LEGACY_ENV,
        )
        # If level is an int (logging.INFO), return its respective string ("INFO")
        if isinstance(level, int):
            return logging.getLevelName(level)

        return level or log_level_env

    def _determine_log_level(self, level: str | int | None) -> str | int:
        """Determine the effective log level considering Lambda and Powertools preferences.
        It emits an UserWarning if Lambda ALC log level is lower than Logger log level.
        Parameters:
        -----------
        level: str | int | None
            The specified log level as a string, integer, or None.
        Returns:
        ----------
            str | int: The effective logging level.
        """

        # This function consider the following order of precedence:
        # 1 - If a log level is set using AWS Lambda Advanced Logging Controls, it sets it.
        # 2 - If a log level is passed to the constructor, it sets it
        # 3 - If a log level is set via setLevel, it sets it.
        # 4 - If a log level is set via Powertools env variables, it sets it.
        # 5 - If none of the above is true, the default log level applies INFO.

        lambda_log_level = self._get_aws_lambda_log_level()
        powertools_log_level = self._get_powertools_log_level(level)

        if powertools_log_level and lambda_log_level:
            # If Powertools log level is set and higher than AWS Lambda Advanced Logging Controls, emit a warning
            if logging.getLevelName(lambda_log_level) > logging.getLevelName(powertools_log_level):
                warnings.warn(
                    f"Current log level ({powertools_log_level}) does not match AWS Lambda Advanced Logging Controls "
                    f"minimum log level ({lambda_log_level}). This can lead to data loss, consider adjusting them.",
                    UserWarning,
                    stacklevel=2,
                )

            # Check if buffer level is less verbose than ALC
            if (
                hasattr(self, "_buffer_config")
                and self._buffer_config
                and logging.getLevelName(lambda_log_level)
                > logging.getLevelName(self._buffer_config.buffer_at_verbosity)
            ):
                warnings.warn(
                    "Advanced Logging Controls (ALC) Log Level is less verbose than Log Buffering Log Level. "
                    "Buffered logs will be filtered by ALC",
                    PowertoolsUserWarning,
                    stacklevel=2,
                )

        # AWS Lambda Advanced Logging Controls takes precedence over Powertools log level and we use this
        if lambda_log_level:
            return lambda_log_level

        # Check if Powertools log level is None, which means it's not set
        # We assume INFO as the default log level
        if powertools_log_level is None:
            return logging.INFO

        # Powertools log level is set, we use this
        return powertools_log_level.upper()

    # FUNCTIONS for Buffering log

    def _create_and_flush_log_record(self, log_line: dict) -> None:
        """
        Create and immediately flush a log record to the configured logger.

        Parameters
        ----------
        log_line : dict[str, Any]
            Dictionary containing log record details with keys:
            - 'level': Logging level
            - 'filename': Source filename
            - 'line': Line number
            - 'msg': Log message
            - 'function': Source function name
            - 'extra': Additional context
            - 'timestamp': Original log creation time

        Notes
        -----
        Bypasses standard logging flow by directly creating and handling a log record.
        Preserves original timestamp and source information.
        """
        record = self._logger.makeRecord(
            name=self.name,
            level=log_line["level"],
            fn=log_line["filename"],
            lno=log_line["line"],
            msg=log_line["msg"],
            args=(),
            exc_info=log_line["exc_info"],
            func=log_line["function"],
            extra=log_line["extra"],
        )
        record.created = log_line["timestamp"]
        self._logger.handle(record)

    def _add_log_record_to_buffer(
        self,
        level: int,
        msg: object,
        args: object,
        exc_info: logging._ExcInfoType = None,
        stack_info: bool = False,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        """
        Add log record to buffer with intelligent tracer ID handling.

        Parameters
        ----------
        level : int
            Logging level of the record.
        msg : object
            Log message to be recorded.
        args : object
            Additional arguments for the log message.
        exc_info : logging._ExcInfoType, optional
            Exception information for the log record.
        stack_info : bool, optional
            Whether to include stack information.
        extra : Mapping[str, object], optional
            Additional contextual information for the log record.

        Raises
        ------
        InvalidBufferItem
            If the log record cannot be added to the buffer.

        Notes
        -----
        Handles special first invocation buffering and migration of log records
        between different tracer contexts.
        """

        # Determine tracer ID, defaulting to first invoke marker
        tracer_id = get_tracer_id()

        if tracer_id and self._buffer_config:
            if not self._buffer_cache.get(tracer_id):
                # Detect new Lambda invocation context and reset buffer to maintain log isolation
                # Ensures logs from previous invocations do not leak into current execution
                # Prevent memory excessive usage
                self._buffer_cache.clear()

            log_record: dict[str, Any] = _create_buffer_record(
                level=level,
                msg=msg,
                args=args,
                exc_info=exc_info,
                stack_info=stack_info,
                extra=extra,
            )
            try:
                self._buffer_cache.add(tracer_id, log_record)
            except BufferError:
                warnings.warn(
                    message="Cannot add item to the buffer. "
                    f"Item size exceeds total cache size {self._buffer_config.max_bytes} bytes",
                    category=PowertoolsUserWarning,
                    stacklevel=2,
                )

                # flush this log to avoid data loss
                self._create_and_flush_log_record(log_record)

    def flush_buffer(self) -> None:
        """
        Flush all buffered log records associated with current execution.

        Notes
        -----
        Retrieves log records for current trace from buffer
        Immediately processes and logs each record
        Warning if some cache was evicted in that execution
        Clears buffer after complete processing

        Raises
        ------
        Any exceptions from underlying logging or buffer mechanisms
        will be propagated to caller
        """

        tracer_id = get_tracer_id()

        # Flushing log without a tracer id? Return
        if not tracer_id:
            return

        # is buffer empty? return
        buffer = self._buffer_cache.get(tracer_id)
        if not buffer:
            return

        if not self._buffer_config:
            return

        # Check ALC level against buffer level
        lambda_log_level = self._get_aws_lambda_log_level()
        if lambda_log_level:
            # Check if buffer level is less verbose than ALC
            if logging.getLevelName(lambda_log_level) > logging.getLevelName(self._buffer_config.buffer_at_verbosity):
                warnings.warn(
                    "Advanced Logging Controls (ALC) Log Level is less verbose than Log Buffering Log Level. "
                    "Some logs might be missing",
                    PowertoolsUserWarning,
                    stacklevel=2,
                )

        # Process log records
        for log_line in buffer:
            self._create_and_flush_log_record(log_line)

        # Has items evicted?
        if self._buffer_cache.has_items_evicted(tracer_id):
            warnings.warn(
                message="Some logs are not displayed because they were evicted from the buffer. "
                "Increase buffer size to store more logs in the buffer",
                category=PowertoolsUserWarning,
                stacklevel=2,
            )

        # Clear the entire cache
        self._buffer_cache.clear()

    def clear_buffer(self) -> None:
        """
        Clear the internal buffer cache.

        This method removes all items from the buffer cache, effectively resetting it to an empty state.

        Returns
        -------
        None
        """
        if self._buffer_config:
            self._buffer_cache.clear()


def set_package_logger(
    level: str | int = logging.DEBUG,
    stream: IO[str] | None = None,
    formatter: logging.Formatter | None = None,
) -> None:
    """Set an additional stream handler, formatter, and log level for aws_lambda_powertools package logger.

    **Package log by default is suppressed (NullHandler), this should only used for debugging.
    This is separate from application Logger class utility**

    Example
    -------
    **Enables debug logging for Powertools for AWS Lambda (Python) package**

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


def log_uncaught_exception_hook(exc_type, exc_value, exc_traceback, logger: Logger) -> None:
    """Callback function for sys.excepthook to use Logger to log uncaught exceptions"""
    logger.exception(exc_value, exc_info=(exc_type, exc_value, exc_traceback))  # pragma: no cover


def _get_caller_filename() -> str:
    """Return caller filename by finding the caller frame"""
    # Current frame         => _get_logger()
    # Previous frame        => logger.py
    # Before previous frame => Caller
    # We ignore mypy here because *we* know that there will always be at least
    # 3 frames (above) so repeatedly calling f_back is safe here
    frame = inspect.currentframe()
    caller_frame = frame.f_back.f_back.f_back  # type: ignore[union-attr]
    return caller_frame.f_globals["__name__"]  # type: ignore[union-attr]
