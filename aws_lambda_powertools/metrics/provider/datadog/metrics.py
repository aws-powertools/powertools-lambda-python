# NOTE: keeps for compatibility
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from aws_lambda_powertools.metrics.provider.datadog.datadog import DEFAULT_NAMESPACE, DatadogProvider


class DatadogMetrics:
    # NOTE: We use class attrs to share metrics data across instances
    # this allows customers to initialize Metrics() throughout their code base (and middlewares)
    # and not get caught by accident with metrics data loss, or data deduplication
    # e.g., m1 and m2 add metric ProductCreated, however m1 has 'version' dimension  but m2 doesn't
    # Result: ProductCreated is created twice as we now have 2 different EMF blobs
    _metrics: List = []
    _default_tags: List = []

    def __init__(
        self,
        namespace: str = DEFAULT_NAMESPACE,
        flush_to_log: bool = False,
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
        tags: List | None = None,
        **kwargs: Any,
    ) -> None:
        self.provider.add_metric(name=name, value=value, timestamp=timestamp, tags=tags, **kwargs)

    def serialize_metric_set(self, metrics: List | None = None) -> List:
        return self.provider.serialize_metric_set(metrics=metrics)

    def flush_metrics(self, raise_on_empty_metrics: bool = False) -> None:
        self.provider.flush_metrics(raise_on_empty_metrics=raise_on_empty_metrics)

    def log_metrics(
        self,
        lambda_handler: Callable[[Dict, Any], Any] | Optional[Callable[[Dict, Any, Optional[Dict]], Any]] = None,
        capture_cold_start_metric: bool = False,
        raise_on_empty_metrics: bool = False,
        default_tags: List | None = None,
    ):
        return self.provider.log_metrics(
            lambda_handler=lambda_handler,
            capture_cold_start_metric=capture_cold_start_metric,
            raise_on_empty_metrics=raise_on_empty_metrics,
            default_tags=default_tags,
        )

    def set_default_tags(self, **kwargs) -> None:
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
        self.provider.set_default_tags(**kwargs)
        for tag_key, tag_value in kwargs.items():
            self.default_tags.append(f"{tag_key}:{tag_value}")

    def clear_metrics(self) -> None:
        self.provider.clear_metrics()

    def clear_default_tags(self) -> None:
        self.provider.default_tags.clear()
        self.default_tags.clear()

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
