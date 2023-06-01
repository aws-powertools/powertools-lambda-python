from __future__ import annotations

import json
import logging
import numbers
import time
import warnings
from typing import Dict, List, Optional

from aws_lambda_powertools.metrics.exceptions import MetricValueError
from aws_lambda_powertools.metrics.provider import MetricsBase, MetricsProviderBase

logger = logging.getLogger(__name__)

# Check if using datadog layer
try:
    from datadog_lambda.metric import lambda_metric  # type: ignore
except ImportError:
    lambda_metric = None


class DataDogProvider(MetricsProviderBase):
    """Class for datadog provider.
    all datadog metric data will be stored as
    see https://github.com/DataDog/datadog-lambda-python/blob/main/datadog_lambda/metric.py#L77
    {
        "m": metric_name,
        "v": value,
        "e": timestamp
        "t": List["tag:value","tag2:value2"]
    }
    """

    def __init__(self, namespace):
        self.metrics = []
        self.namespace = namespace
        super().__init__()

    #  adding name,value,timestamp,tags
    # consider directly calling lambda_metric function here
    def add_metric(self, name: str, value: float, timestamp: Optional[int] = None, tags: Optional[List] = None):
        if not isinstance(value, numbers.Real):
            raise MetricValueError(f"{value} is not a valid number")
        if not timestamp:
            timestamp = time.time()
        self.metrics.append({"m": name, "v": int(value), "e": timestamp, "t": tags})

    # serialize for flushing
    def serialize(self) -> Dict:
        # logic here is to add dimension and metadata to each metric's tag with "key:value" format
        extra_tags: List = []
        output_list: List = []

        for single_metric in self.metrics:
            output_list.append(
                {
                    "m": f"{self.namespace}.{single_metric['m']}",
                    "v": single_metric["v"],
                    "e": single_metric["e"],
                    "t": single_metric["t"] + extra_tags,
                }
            )

        return {"List": output_list}

    # flush serialized data to output
    def flush(self, metrics):
        # submit through datadog extension
        if lambda_metric:
            # use lambda_metric function from datadog package, submit metrics to datadog
            for metric_item in metrics.get("List"):
                lambda_metric(
                    metric_name=metric_item["m"],
                    value=metric_item["v"],
                    timestamp=metric_item["e"],
                    tags=metric_item["t"],
                )
        else:
            # flush to log with datadog format
            # https://github.com/DataDog/datadog-lambda-python/blob/main/datadog_lambda/metric.py#L77
            for metric_item in metrics.get("List"):
                print(json.dumps(metric_item, separators=(",", ":")))

    def clear(self):
        self.metrics = []


class DataDogMetrics(MetricsBase):
    """Class for datadog metrics standalone class.

    Example
    -------
    dd_provider = DataDogProvider(namespace="default")
    metrics = DataDogMetrics(provider=dd_provider)

    @metrics.log_metrics(capture_cold_start_metric: bool = True, raise_on_empty_metrics: bool = False)
    def lambda_handler(event, context)
        metrics.add_metric(name="item_sold",value=1,tags)
    """

    # `log_metrics` and `_add_cold_start_metric` are directly inherited from `MetricsBase`
    def __init__(self, provider):
        self.provider = provider
        super().__init__()

    def add_metric(self, name: str, value: float, timestamp: Optional[int] = None, tags: Optional[List] = None):
        self.provider.add_metric(name=name, value=value, timestamp=timestamp, tags=tags)

    def flush_metrics(self, raise_on_empty_metrics: bool = False) -> None:
        metrics = self.provider.serialize()
        if not metrics and raise_on_empty_metrics:
            warnings.warn(
                "No application metrics to publish. The cold-start metric may be published if enabled. "
                "If application metrics should never be empty, consider using 'raise_on_empty_metrics'",
                stacklevel=2,
            )
        self.provider.flush(metrics)
        self.provider.clear()
