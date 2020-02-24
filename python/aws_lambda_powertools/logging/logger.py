import functools
import itertools
import logging
import os
import random
from distutils.util import strtobool
from typing import Any, Callable, Dict

from ..helper.models import MetricUnit, build_lambda_context_model, build_metric_unit_from_str
from . import aws_lambda_logging

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

is_cold_start = True


def logger_setup(service: str = "service_undefined", level: str = "INFO", sampling_rate: float = 0.0, **kwargs):
    """Setups root logger to format statements in JSON.

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
    level : str, optional
        logging.level, by default "INFO"
    sample_rate: float, optional
        sample rate for debug calls within execution context defaults to 0

    Example
    -------
    Setups structured logging in JSON for Lambda functions with explicit service name

        >>> from aws_lambda_powertools.logging import logger_setup
        >>> logger = logger_setup(service="payment")
        >>>
        >>> def handler(event, context):
                logger.info("Hello")

    Setups structured logging in JSON for Lambda functions using env vars

        $ export POWERTOOLS_SERVICE_NAME="payment"
        $ export POWERTOOLS_LOGGER_SAMPLE_RATE=0.01 # 1% debug sampling
        >>> from aws_lambda_powertools.logging import logger_setup
        >>> logger = logger_setup()
        >>>
        >>> def handler(event, context):
                logger.info("Hello")

    """
    service = os.getenv("POWERTOOLS_SERVICE_NAME") or service
    sampling_rate = os.getenv("POWERTOOLS_LOGGER_SAMPLE_RATE") or sampling_rate
    log_level = os.getenv("LOG_LEVEL") or level
    logger = logging.getLogger(name=service)

    try:
        if sampling_rate and random.random() <= float(sampling_rate):
            log_level = logging.DEBUG
    except ValueError:  
        raise ValueError(
            "fExpected a float value ranging 0 to 1, but received {sampling_rate} instead. Please review POWERTOOLS_LOGGER_SAMPLE_RATE environment variable."
        )

    logger.setLevel(log_level)

    # Patch logger by structuring its outputs as JSON
    aws_lambda_logging.setup(level=log_level, service=service, sampling_rate=sampling_rate, **kwargs)

    return logger


def logger_inject_lambda_context(lambda_handler: Callable[[Dict, Any], Any] = None, log_event: bool = False):
    """Decorator to capture Lambda contextual info and inject into struct logging

    Parameters
    ----------
    log_event : bool, optional
        Instructs logger to log Lambda Event, by default False

    Environment variables
    ---------------------
    POWERTOOLS_LOGGER_LOG_EVENT : str
        instruct logger to log Lambda Event (e.g. "true", "True", "TRUE")

    Example
    -------
    Captures Lambda contextual runtime info (e.g memory, arn, req_id)
        >>> from aws_lambda_powertools.logging import logger_setup, logger_inject_lambda_context
        >>> import logging
        >>>
        >>> logger = logging.getLogger(__name__)
        >>> logging.setLevel(logging.INFO)
        >>> logger_setup()
        >>>
        >>> @logger_inject_lambda_context
        >>> def handler(event, context):
                logger.info("Hello")

    Captures Lambda contextual runtime info and logs incoming request
        >>> from aws_lambda_powertools.logging import logger_setup, logger_inject_lambda_context
        >>> import logging
        >>>
        >>> logger = logging.getLogger(__name__)
        >>> logging.setLevel(logging.INFO)
        >>> logger_setup()
        >>>
        >>> @logger_inject_lambda_context(log_event=True)
        >>> def handler(event, context):
                logger.info("Hello")

    Returns
    -------
    decorate : Callable
        Decorated lambda handler
    """

    # If handler is None we've been called with parameters
    # We then return a partial function with args filled
    # Next time we're called we'll call our Lambda
    # This allows us to avoid writing wrapper_wrapper type of fn
    if lambda_handler is None:
        logger.debug("Decorator called with parameters")
        return functools.partial(logger_inject_lambda_context, log_event=log_event)

    log_event_env_option = str(os.getenv("POWERTOOLS_LOGGER_LOG_EVENT", "false"))
    log_event = strtobool(log_event_env_option) or log_event

    @functools.wraps(lambda_handler)
    def decorate(event, context):
        if log_event:
            logger.debug("Event received")
            logger.info(event)

        lambda_context = build_lambda_context_model(context)
        cold_start = __is_cold_start()

        logger_setup(cold_start=cold_start, **lambda_context.__dict__)

        return lambda_handler(event, context)

    return decorate


def __is_cold_start() -> str:
    """Verifies whether is cold start and return a string used for struct logging

    Returns
    -------
    str
        lower case bool as a string
        aws_lambda_logging doesn't support bool; cast cold start value to string
    """
    cold_start = "false"

    global is_cold_start
    if is_cold_start:
        cold_start = str(is_cold_start).lower()
        is_cold_start = False

    return cold_start


def log_metric(
    name: str, namespace: str, unit: MetricUnit, value: float = 0, service: str = "service_undefined", **dimensions,
):
    """Logs a custom metric in a statsD-esque format to stdout.

    Creating Custom Metrics synchronously impact on performance/execution time.
    Instead, log_metric prints a metric to CloudWatch Logs.
    That allows us to pick them up asynchronously via another Lambda function and create them as a metric.

    NOTE: It takes up to 9 dimensions by default, and Metric units are conveniently available via MetricUnit Enum.
    If service is not passed as arg or via env var, "service_undefined" will be used as dimension instead.

    Output in CloudWatch Logs: MONITORING|<metric_value>|<metric_unit>|<metric_name>|<namespace>|<dimensions>

    Serverless Application Repository App that creates custom metric from this log output:
    https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:374852340823:applications~async-custom-metrics

    Environment variables
    ---------------------
    POWERTOOLS_SERVICE_NAME: str
        service name

    Example
    -------
    Log metric to count number of successful payments; define service via env var

        $ export POWERTOOLS_SERVICE_NAME="payment"
        >>> from aws_lambda_powertools.logging import MetricUnit, log_metric
        >>> log_metric(
            name="SuccessfulPayments",
            unit=MetricUnit.Count,
            value=1,
            namespace="DemoApp"
        )

    Log metric to count number of successful payments per campaign & customer

        >>> from aws_lambda_powertools.logging import MetricUnit, log_metric
        >>> log_metric(
            name="SuccessfulPayments",
            service="payment",
            unit=MetricUnit.Count,
            value=1,
            namespace="DemoApp",
            campaign=campaign_id,
            customer=customer_id
        )

    Parameters
    ----------
    name : str
        metric name, by default None
    namespace : str
        metric namespace (e.g. application name), by default None
    unit : MetricUnit, by default MetricUnit.Count
        metric unit enum value (e.g. MetricUnit.Seconds), by default None
        API Info: https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html
    value : float, optional
        metric value, by default 0
    service : str, optional
        service name used as dimension, by default "service_undefined"
    dimensions: dict, optional
        keyword arguments as additional dimensions (e.g. customer=customerId)
    """

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
