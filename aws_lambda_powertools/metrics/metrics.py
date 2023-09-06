# NOTE: keeps for compatibility
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from aws_lambda_powertools.metrics.base import MetricResolution, MetricUnit
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.cloudwatch import AmazonCloudWatchEMFProvider
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.types import CloudWatchEMFOutput


class Metrics:
    """Metrics create an CloudWatch EMF object with up to 100 metrics

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

        @metrics.log_metrics(capture_cold_start_metric=True)
        def lambda_handler():
            metrics.add_metric(name="BookingConfirmation", unit="Count", value=1)
            metrics.add_dimension(name="function_version", value="$LATEST")

            return True

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
    namespace : str, optional
        Namespace for metrics
    provider: AmazonCloudWatchEMFProvider, optional
        Pre-configured AmazonCloudWatchEMFProvider provider

    Raises
    ------
    MetricUnitError
        When metric unit isn't supported by CloudWatch
    MetricResolutionError
        When metric resolution isn't supported by CloudWatch
    MetricValueError
        When metric value isn't a number
    SchemaValidationError
        When metric object fails EMF schema validation
    """

    # NOTE: We use class attrs to share metrics data across instances
    # this allows customers to initialize Metrics() throughout their code base (and middlewares)
    # and not get caught by accident with metrics data loss, or data deduplication
    # e.g., m1 and m2 add metric ProductCreated, however m1 has 'version' dimension  but m2 doesn't
    # Result: ProductCreated is created twice as we now have 2 different EMF blobs
    _metrics: Dict[str, Any] = {}
    _dimensions: Dict[str, str] = {}
    _metadata: Dict[str, Any] = {}
    _default_dimensions: Dict[str, Any] = {}

    def __init__(
        self,
        service: str | None = None,
        namespace: str | None = None,
        provider: AmazonCloudWatchEMFProvider | None = None,
    ):
        self.metric_set = self._metrics
        self.metadata_set = self._metadata
        self.default_dimensions = self._default_dimensions
        self.dimension_set = self._dimensions

        self.dimension_set.update(**self._default_dimensions)

        if provider is None:
            self.provider = AmazonCloudWatchEMFProvider(
                namespace=namespace,
                service=service,
                metric_set=self.metric_set,
                dimension_set=self.dimension_set,
                metadata_set=self.metadata_set,
                default_dimensions=self._default_dimensions,
            )
        else:
            self.provider = provider

    def add_metric(
        self,
        name: str,
        unit: MetricUnit | str,
        value: float,
        resolution: MetricResolution | int = 60,
    ) -> None:
        self.provider.add_metric(name=name, unit=unit, value=value, resolution=resolution)

    def add_dimension(self, name: str, value: str) -> None:
        self.provider.add_dimension(name=name, value=value)

    def serialize_metric_set(
        self,
        metrics: Dict | None = None,
        dimensions: Dict | None = None,
        metadata: Dict | None = None,
    ) -> CloudWatchEMFOutput:
        return self.provider.serialize_metric_set(metrics=metrics, dimensions=dimensions, metadata=metadata)

    def add_metadata(self, key: str, value: Any) -> None:
        self.provider.add_metadata(key=key, value=value)

    def flush_metrics(self, raise_on_empty_metrics: bool = False) -> None:
        self.provider.flush_metrics(raise_on_empty_metrics=raise_on_empty_metrics)

    def log_metrics(
        self,
        lambda_handler: Callable[[Dict, Any], Any] | Optional[Callable[[Dict, Any, Optional[Dict]], Any]] = None,
        capture_cold_start_metric: bool = False,
        raise_on_empty_metrics: bool = False,
        default_dimensions: Dict[str, str] | None = None,
    ):
        return self.provider.log_metrics(
            lambda_handler=lambda_handler,
            capture_cold_start_metric=capture_cold_start_metric,
            raise_on_empty_metrics=raise_on_empty_metrics,
            default_dimensions=default_dimensions,
        )

    def set_default_dimensions(self, **dimensions) -> None:
        self.provider.set_default_dimensions(**dimensions)
        """Persist dimensions across Lambda invocations

        Parameters
        ----------
        dimensions : Dict[str, Any], optional
            metric dimensions as key=value

        Example
        -------
        **Sets some default dimensions that will always be present across metrics and invocations**

            from aws_lambda_powertools import Metrics

            metrics = Metrics(namespace="ServerlessAirline", service="payment")
            metrics.set_default_dimensions(environment="demo", another="one")

            @metrics.log_metrics()
            def lambda_handler():
                return True
        """
        for name, value in dimensions.items():
            self.add_dimension(name, value)

        self.default_dimensions.update(**dimensions)

    def clear_default_dimensions(self) -> None:
        self.provider.default_dimensions.clear()
        self.default_dimensions.clear()

    def clear_metrics(self) -> None:
        self.provider.clear_metrics()

    # We now allow customers to bring their own instance
    # of the AmazonCloudWatchEMFProvider provider
    # So we need to define getter/setter for namespace and service properties
    # To access these attributes on the provider instance.
    @property
    def namespace(self):
        return self.provider.namespace

    @namespace.setter
    def namespace(self, namespace):
        self.provider.namespace = namespace

    @property
    def service(self):
        return self.provider.service

    @service.setter
    def service(self, service):
        self.provider.service = service


# Maintenance: until v3, we can't afford to break customers.
# AmazonCloudWatchEMFProvider has the exact same functionality (non-singleton)
# so we simply alias. If a customer subclassed `EphemeralMetrics` and somehow relied on __name__
# we can quickly revert and duplicate code while using self.provider

EphemeralMetrics = AmazonCloudWatchEMFProvider
