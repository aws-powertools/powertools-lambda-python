import copy
import functools
import itertools
import json
import logging
import os
import random
import sys
import warnings
from distutils.util import strtobool
from typing import Any, Callable, Dict, Union

from ..helper.models import MetricUnit, build_lambda_context_model, build_metric_unit_from_str
from .exceptions import InvalidLoggerSamplingRateError

logger = logging.getLogger(__name__)

is_cold_start = True


def json_formatter(unserialized_value: Any):
    """JSON custom serializer to cast unserialisable values to strings.

    Example
    -------

    **Serialize unserialisable value to string**

        class X: pass
        value = {"x": X()}

        json.dumps(value, default=json_formatter)

    Parameters
    ----------
    unserialized_value: Any
        Python object unserializable by JSON
    """
    return str(unserialized_value)


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
        unserialisable values.  It must not throw.  Defaults to a function that
        coerces the value to a string.

        Other kwargs are used to specify log field format strings.
        """
        datefmt = kwargs.pop("datefmt", None)

        super(JsonFormatter, self).__init__(datefmt=datefmt)
        self.reserved_keys = ["timestamp", "level", "location"]
        self.format_dict = {
            "timestamp": "%(asctime)s",
            "level": "%(levelname)s",
            "location": "%(funcName)s:%(lineno)d",
        }
        self.format_dict.update(kwargs)
        self.default_json_formatter = kwargs.pop("json_default", json_formatter)

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


def logger_setup(
    service: str = None, level: str = None, sampling_rate: float = 0.0, legacy: bool = False, **kwargs
) -> DeprecationWarning:
    """DEPRECATED

    This will be removed when GA - Use `aws_lambda_powertools.logging.logger.Logger` instead

    Example
    -------
        **Logger class - Same UX**

        from aws_lambda_powertools import Logger
        logger = Logger(service="payment") # same env var still applies

    """
    raise DeprecationWarning("Use Logger instead - This method will be removed when GA")


def logger_inject_lambda_context(
    lambda_handler: Callable[[Dict, Any], Any] = None, log_event: bool = False
) -> DeprecationWarning:
    """DEPRECATED

    This will be removed when GA - Use `aws_lambda_powertools.logging.logger.Logger` instead

    Example
    -------
        **Logger class - Same UX**

        from aws_lambda_powertools import Logger
        logger = Logger(service="payment") # same env var still applies
        @logger.inject_lambda_context
        def handler(evt, ctx):
            pass
    """
    raise DeprecationWarning("Use Logger instead - This method will be removed when GA")


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


def log_metric(
    name: str, namespace: str, unit: MetricUnit, value: float = 0, service: str = "service_undefined", **dimensions,
):
    """Logs a custom metric in a statsD-esque format to stdout.

    **This will be removed when GA - Use `aws_lambda_powertools.metrics.metrics.Metrics` instead**

    Creating Custom Metrics synchronously impact on performance/execution time.
    Instead, log_metric prints a metric to CloudWatch Logs.
    That allows us to pick them up asynchronously via another Lambda function and create them as a metric.

    NOTE: It takes up to 9 dimensions by default, and Metric units are conveniently available via MetricUnit Enum.
    If service is not passed as arg or via env var, "service_undefined" will be used as dimension instead.

    **Output in CloudWatch Logs**: `MONITORING|<metric_value>|<metric_unit>|<metric_name>|<namespace>|<dimensions>`

    Serverless Application Repository App that creates custom metric from this log output:
    https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:374852340823:applications~async-custom-metrics

    Environment variables
    ---------------------
    POWERTOOLS_SERVICE_NAME: str
        service name

    Parameters
    ----------
    name : str
        metric name, by default None
    namespace : str
        metric namespace (e.g. application name), by default None
    unit : MetricUnit, by default MetricUnit.Count
        metric unit enum value (e.g. MetricUnit.Seconds), by default None\n
        API Info: https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html
    value : float, optional
        metric value, by default 0
    service : str, optional
        service name used as dimension, by default "service_undefined"
    dimensions: dict, optional
        keyword arguments as additional dimensions (e.g. `customer=customerId`)

    Example
    -------
    **Log metric to count number of successful payments; define service via env var**

        $ export POWERTOOLS_SERVICE_NAME="payment"
        from aws_lambda_powertools.logging import MetricUnit, log_metric
        log_metric(
            name="SuccessfulPayments",
            unit=MetricUnit.Count,
            value=1,
            namespace="DemoApp"
        )

    **Log metric to count number of successful payments per campaign & customer**

        from aws_lambda_powertools.logging import MetricUnit, log_metric
        log_metric(
            name="SuccessfulPayments",
            service="payment",
            unit=MetricUnit.Count,
            value=1,
            namespace="DemoApp",
            campaign=campaign_id,
            customer=customer_id
        )
    """

    warnings.warn(message="This method will be removed in GA; use Metrics instead", category=DeprecationWarning)
    logger.debug(f"Building new custom metric. Name: {name}, Unit: {unit}, Value: {value}, Dimensions: {dimensions}")
    service = os.getenv("POWERTOOLS_SERVICE_NAME") or service
    dimensions = __build_dimensions(**dimensions)
    unit = build_metric_unit_from_str(unit)

    metric = f"MONITORING|{value}|{unit.name}|{name}|{namespace}|service={service}"
    if dimensions:
        metric = f"MONITORING|{value}|{unit.name}|{name}|{namespace}|service={service},{dimensions}"

    print(metric)


def __build_dimensions(**dimensions) -> str:
    """Builds correct format for custom metric dimensions from kwargs

    Parameters
    ----------
    dimensions: dict, optional
        additional dimensions

    Returns
    -------
    str
        Dimensions in the form of "key=value,key2=value2"
    """
    MAX_DIMENSIONS = 10
    dimension = ""

    # CloudWatch accepts a max of 10 dimensions per metric
    # We include service name as a dimension
    # so we take up to 9 values as additional dimensions
    # before we convert everything to a string of key=value
    dimensions_partition = dict(itertools.islice(dimensions.items(), MAX_DIMENSIONS))
    dimensions_list = [dimension + "=" + value for dimension, value in dimensions_partition.items() if value]
    dimension = ",".join(dimensions_list)

    return dimension


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
