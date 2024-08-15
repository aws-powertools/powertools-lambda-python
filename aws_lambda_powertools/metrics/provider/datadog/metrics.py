# NOTE: keeps for compatibility
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.metrics.provider.datadog.datadog import DatadogProvider

if TYPE_CHECKING:
    from aws_lambda_powertools.shared.types import AnyCallableT


class DatadogMetrics:
    """
    DatadogProvider creates metrics asynchronously via Datadog extension or exporter.

    **Use `aws_lambda_powertools.DatadogMetrics` to create and metrics to Datadog.**

    Example
    -------
    **Creates a few metrics and publish at the end of a function execution**

        from aws_lambda_powertools.metrics.provider.datadog import DatadogMetrics

        metrics = DatadogMetrics(namespace="ServerlessAirline")

        @metrics.log_metrics(capture_cold_start_metric=True)
        def lambda_handler():
            metrics.add_metric(name="item_sold", value=1, product="latte", order="online")
            return True

    Environment variables
    ---------------------
    POWERTOOLS_METRICS_NAMESPACE : str
        metric namespace

    Parameters
    ----------
    flush_to_log : bool, optional
        Used when using export instead of Lambda Extension
    namespace : str, optional
        Namespace for metrics
    provider: DatadogProvider, optional
        Pre-configured DatadogProvider provider

    Raises
    ------
    MetricValueError
        When metric value isn't a number
    SchemaValidationError
        When metric object fails Datadog schema validation
    """

    # NOTE: We use class attrs to share metrics data across instances
    # this allows customers to initialize Metrics() throughout their code base (and middlewares)
    # and not get caught by accident with metrics data loss, or data deduplication
    # e.g., m1 and m2 add metric ProductCreated, however m1 has 'version' dimension  but m2 doesn't
    # Result: ProductCreated is created twice as we now have 2 different EMF blobs
    _metrics: list = []
    _default_tags: dict[str, Any] = {}

    def __init__(
        self,
        namespace: str | None = None,
        flush_to_log: bool | None = None,
        provider: DatadogProvider | None = None,
    ):
        self.metric_set = self._metrics
        self.default_tags = self._default_tags

        if provider is None:
            self.provider = DatadogProvider(
                namespace=namespace,
                flush_to_log=flush_to_log,
                metric_set=self.metric_set,
            )
        else:
            self.provider = provider

    def add_metric(
        self,
        name: str,
        value: float,
        timestamp: int | None = None,
        **tags: Any,
    ) -> None:
        self.provider.add_metric(name=name, value=value, timestamp=timestamp, **tags)

    def serialize_metric_set(self, metrics: list | None = None) -> list:
        return self.provider.serialize_metric_set(metrics=metrics)

    def flush_metrics(self, raise_on_empty_metrics: bool = False) -> None:
        self.provider.flush_metrics(raise_on_empty_metrics=raise_on_empty_metrics)

    def log_metrics(
        self,
        lambda_handler: AnyCallableT | None = None,
        capture_cold_start_metric: bool = False,
        raise_on_empty_metrics: bool = False,
        default_tags: dict[str, Any] | None = None,
    ):
        return self.provider.log_metrics(
            lambda_handler=lambda_handler,
            capture_cold_start_metric=capture_cold_start_metric,
            raise_on_empty_metrics=raise_on_empty_metrics,
            default_tags=default_tags,
        )

    def set_default_tags(self, **tags) -> None:
        self.provider.set_default_tags(**tags)
        self.default_tags.update(**tags)

    def clear_metrics(self) -> None:
        self.provider.clear_metrics()

    def clear_default_tags(self) -> None:
        self.provider.default_tags.clear()
        self.default_tags.clear()

    # We now allow customers to bring their own instance
    # of the DatadogProvider provider
    # So we need to define getter/setter for namespace property
    # To access this attribute on the provider instance.
    @property
    def namespace(self):
        return self.provider.namespace

    @namespace.setter
    def namespace(self, namespace):
        self.provider.namespace = namespace
