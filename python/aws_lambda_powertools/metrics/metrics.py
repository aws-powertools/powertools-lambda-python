import functools
import json
import logging
import os
from typing import Any, Callable

from aws_lambda_powertools.metrics.base import MetricManager

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


class Metrics(MetricManager):
    """Metrics create an EMF object with up to 100 metrics

    Use Metrics when you need to create multiple metrics that have
    dimensions in common (e.g. service_name="payment").

    Metrics up to 100 metrics in memory and are shared across
    all its instances. That means it can be safely instantiated outside
    of a Lambda function, or anywhere else.

    A decorator (log_metrics) is provided so metrics are published at the end of its execution.
    If more than 100 metrics are added at a given function execution,
    these metrics are serialized and published before adding a given metric
    to prevent metric truncation.

    Example
    -------
    **Creates a few metrics and publish at the end of a function execution**

        from aws_lambda_powertools.metrics import Metrics

        metrics = Metrics()
        metrics.add_namespace(name="ServerlessAirline")
        metrics.add_metric(name="ColdStart", unit=MetricUnit.Count, value=1)
        metrics.add_metric(name="BookingConfirmation", unit="Count", value=1)
        metrics.add_dimension(name="service", value="booking")
        metrics.add_dimension(name="function_version", value="$LATEST")
        ...

        @tracer.capture_lambda_handler
        @metrics.log_metrics()
        def lambda_handler():
                do_something()
                return True

        def do_something():
                metrics.add_metric(name="Something", unit="Count", value=1)

    **Calls lambda function and creates a few metrics and publish.** \n
    Useful when log_metrics is the only decorator used, or when no other decorator calls the handler

        from aws_lambda_powertools.metrics import Metrics
        metrics = Metrics()
        metrics.add_namespace(name="ServerlessAirline")
        metrics.add_dimension(name="service", value="booking")
        metrics.add_dimension(name="function_version", value="$LATEST")
        ...
        @metrics.log_metrics(call_function=True)
        def lambda_handler():
                if cold_start:
                    metrics.add_metric(name="ColdStart", unit=MetricUnit.Count, value=1)
                    metrics.add_metric(name="BookingConfirmation", unit="Count", value=1)
                do_something()
                return True

        def do_something():
                metrics.add_metric


    Environment variables
    ---------------------
    POWERTOOLS_METRICS_NAMESPACE : str
        metric namespace

    Parameters
    ----------
    MetricManager : MetricManager
        Inherits from `aws_lambda_powertools.metrics.base.MetricManager`

    Raises
    ------
    e
        Propagate error received
    """

    _metrics = {}
    _dimensions = {}

    def __init__(self, metric_set=None, dimension_set=None, namespace=None):
        super().__init__(metric_set=self._metrics, dimension_set=self._dimensions, namespace=namespace)

    def log_metrics(self, lambda_handler: Callable[[Any, Any], Any] = None, call_function: bool = False):
        """Decorator to serialize and publish metrics at the end of a function execution.

        By default, log_metrics doesn't run the method it decorates (lambda handler). However,
        if you are only using Metrics feature, you can change that behaviour with
        `call_function` parameter.

        Example
        -------
        **Lambda function using tracer and metrics decorators**

            metrics = Metrics()
            tracer = Tracer(service="payment")

            @tracer.capture_lambda_handler
            @metrics.log_metrics
                def handler(event, context)

        **Lambda function using metrics decorator only**

            metrics = Metrics()
            @metrics.log_metrics(call_function=True)
                def handler(event, context)

        Parameters
        ----------
        lambda_handler : Callable[[Any, Any], Any], optional
            Lambda function handler, by default None
        call_function : bool, optional
            Call function it annotates, by default False

        Raises
        ------
        e
            Propagate error received
        """
        if lambda_handler is None:
            return functools.partial(self.log_metrics, call_function=call_function)

        @functools.wraps(lambda_handler)
        def decorate(*args, **kwargs):
            try:
                if call_function:
                    logger.debug("Calling Lambda handler")
                    lambda_handler(*args, **kwargs)
                metrics = self.serialize_metric_set()
                logger.debug("Publishing metrics", {"metrics": metrics})
                print(json.dumps(metrics))
            except Exception as e:
                logger.error(e)
                raise e

        return decorate
