import functools
import json
import logging
import warnings
from typing import Any, Callable

from .base import MetricManager, MetricUnit
from .metric import single_metric

logger = logging.getLogger(__name__)

is_cold_start = True


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

        from aws_lambda_powertools import Metrics

        metrics = Metrics(namespace="ServerlessAirline", service="payment")
        metrics.add_metric(name="ColdStart", unit=MetricUnit.Count, value=1)
        metrics.add_metric(name="BookingConfirmation", unit="Count", value=1)
        metrics.add_dimension(name="function_version", value="$LATEST")
        ...

        @metrics.log_metrics()
        def lambda_handler():
               do_something()
               return True

        def do_something():
               metrics.add_metric(name="Something", unit="Count", value=1)

    Environment variables
    ---------------------
    POWERTOOLS_METRICS_NAMESPACE : str
        metric namespace
    POWERTOOLS_SERVICE_NAME : str
        service name used for default dimension

    Parameters
    ----------
    service : str, optional
        service name to be used as metric dimension, by default "service_undefined"
    namespace : str
        Namespace for metrics

    Raises
    ------
    MetricUnitError
        When metric metric isn't supported by CloudWatch
    MetricValueError
        When metric value isn't a number
    SchemaValidationError
        When metric object fails EMF schema validation
    """

    _metrics = {}
    _dimensions = {}
    _metadata = {}

    def __init__(self, service: str = None, namespace: str = None):
        self.metric_set = self._metrics
        self.dimension_set = self._dimensions
        self.service = service
        self.namespace = namespace
        self.metadata_set = self._metadata

        super().__init__(
            metric_set=self.metric_set,
            dimension_set=self.dimension_set,
            namespace=self.namespace,
            metadata_set=self.metadata_set,
            service=self.service,
        )

    def clear_metrics(self):
        logger.debug("Clearing out existing metric set from memory")
        self.metric_set.clear()
        self.dimension_set.clear()
        self.metadata_set.clear()

    def log_metrics(
        self,
        lambda_handler: Callable[[Any, Any], Any] = None,
        capture_cold_start_metric: bool = False,
        raise_on_empty_metrics: bool = False,
    ):
        """Decorator to serialize and publish metrics at the end of a function execution.

        Be aware that the log_metrics **does call* the decorated function (e.g. lambda_handler).

        Example
        -------
        **Lambda function using tracer and metrics decorators**

            from aws_lambda_powertools import Metrics, Tracer

            metrics = Metrics(service="payment")
            tracer = Tracer(service="payment")

            @tracer.capture_lambda_handler
            @metrics.log_metrics
            def handler(event, context):
                    ...

        Parameters
        ----------
        lambda_handler : Callable[[Any, Any], Any], optional
            Lambda function handler, by default None
        capture_cold_start_metric : bool, optional
            Captures cold start metric, by default False
        raise_on_empty_metrics : bool, optional
            Raise exception if no metrics are emitted, by default False

        Raises
        ------
        e
            Propagate error received
        """

        # If handler is None we've been called with parameters
        # Return a partial function with args filled
        if lambda_handler is None:
            logger.debug("Decorator called with parameters")
            return functools.partial(
                self.log_metrics,
                capture_cold_start_metric=capture_cold_start_metric,
                raise_on_empty_metrics=raise_on_empty_metrics,
            )

        @functools.wraps(lambda_handler)
        def decorate(event, context):
            try:
                response = lambda_handler(event, context)
                if capture_cold_start_metric:
                    self.__add_cold_start_metric(context=context)
            finally:
                if not raise_on_empty_metrics and not self.metric_set:
                    warnings.warn("No metrics to publish, skipping")
                else:
                    metrics = self.serialize_metric_set()
                    self.clear_metrics()
                    print(json.dumps(metrics, separators=(",", ":")))

            return response

        return decorate

    def __add_cold_start_metric(self, context: Any):
        """Add cold start metric and function_name dimension

        Parameters
        ----------
        context : Any
            Lambda context
        """
        global is_cold_start
        if is_cold_start:
            logger.debug("Adding cold start metric and function_name dimension")
            with single_metric(name="ColdStart", unit=MetricUnit.Count, value=1, namespace=self.namespace) as metric:
                metric.add_dimension(name="function_name", value=context.function_name)
                metric.add_dimension(name="service", value=self.service)
                is_cold_start = False
