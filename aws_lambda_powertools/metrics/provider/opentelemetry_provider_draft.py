from __future__ import annotations

import logging
import numbers
import warnings
from typing import Dict, Optional

from aws_lambda_powertools.metrics.exceptions import MetricValueError
from aws_lambda_powertools.metrics.provider import MetricsBase, MetricsProviderBase

logger = logging.getLogger(__name__)

# Check if using datadog layer
try:
    from opentelemetry import metrics
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        PeriodicExportingMetricReader,
    )
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource

    otlp_metrics = True
except ImportError:
    otlp_metrics = False


class OTLPProvider(MetricsProviderBase):
    """
    Class for OTLP provider.

    """

    def __init__(self, namespace: str = "default", endpoint: str = "localhost:4317"):
        if not otlp_metrics:
            raise Exception("OTLP package not found")
        resource = Resource(attributes={SERVICE_NAME: namespace})

        reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint))
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        # Sets the global default meter provider
        metrics.set_meter_provider(provider)
        self.meter = metrics.get_meter(namespace)
        self.counters: Dict = {}
        super().__init__()

    #  adding name,value,timestamp,tags
    # consider directly calling lambda_metric function here
    def add_metric(self, name: str, value: float, unit: Optional[str] = "1", tags: Optional[Dict] = None):
        if not isinstance(value, numbers.Real):
            raise MetricValueError(f"{value} is not a valid number")
        if name not in self.counters:
            self.counters[name] = self.meter.create_counter(name=name, unit=unit)
        self.counters[name].add(amount=value, attributes=tags)

    # serialize for flushing (Do we really need this function for datadog?)
    def serialize(self):
        # not implemented
        pass

    # flush serialized data to output
    def flush(self):
        # not implemented
        pass


class OTLPMetrics(MetricsBase):
    """Class for datadog metrics standalone class.

    Example
    -------
    dd_provider = OTLPProvider(namespace="default")
    metrics = OTLPMetrics(provider=dd_provider)

    @metrics.log_metrics(capture_cold_start_metric: bool = True, raise_on_empty_metrics: bool = False)
    def lambda_handler(event, context)
        metrics.add_metric(name="item_sold",value=1,tags)
    """

    # `log_metrics` and `_add_cold_start_metric` are directly inherited from `MetricsBase`
    def __init__(self, provider):
        self.provider = provider
        super().__init__()

    # drop additional kwargs to keep same experience
    def add_metric(
        self,
        name: str,
        value: float,
        unit: Optional[str] = "1",
        tags: Optional[Dict] = None,
        *args,
        **kwargs,
    ):
        self.provider.add_metric(name=name, value=value, unit=unit, tags=tags)

    def flush_metrics(self, raise_on_empty_metrics: bool = False) -> None:
        if not self.provider.counters and raise_on_empty_metrics:
            warnings.warn(
                "No application metrics to publish. The cold-start metric may be published if enabled. "
                "If application metrics should never be empty, consider using 'raise_on_empty_metrics'",
                stacklevel=2,
            )
        # not implemented for OTPL
