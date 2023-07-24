from __future__ import annotations

import json
import logging
import numbers
import os
import time
import warnings
from typing import Any, List, Optional

from aws_lambda_powertools.metrics.exceptions import MetricValueError, SchemaValidationError
from aws_lambda_powertools.metrics.provider import MetricsBase, MetricsProviderBase

logger = logging.getLogger(__name__)

# Check if using datadog layer
try:
    from datadog_lambda.metric import lambda_metric  # type: ignore
except ImportError:
    lambda_metric = None

DEFAULT_NAMESPACE = "default"


class DataDogProvider(MetricsProviderBase):
    """
    Class for datadog provider. This Class should only be used inside DataDogMetrics
    all datadog metric data will be stored as
    {
        "m": metric_name,
        "v": value,
        "e": timestamp
        "t": List["tag:value","tag2:value2"]
    }
    see https://github.com/DataDog/datadog-lambda-python/blob/main/datadog_lambda/metric.py#L77

    Examples
    --------

    """

    def __init__(self, namespace: str = DEFAULT_NAMESPACE, flush_to_log: bool = False):
        """

        Parameters
        ----------
        namespace: str
            For datadog, namespace will be appended in front of the metrics name in metrics exported.
            (namespace.metrics_name)
        flush_to_log: bool
            Flush datadog metrics to log (collect with log forwarder) rather than using datadog extension
        """
        self.metrics: List = []
        self.namespace: str = namespace
        # either is true then flush to log
        self.flush_to_log = (os.environ.get("DD_FLUSH_TO_LOG", "").lower() == "true") or flush_to_log
        super().__init__()

    #  adding name,value,timestamp,tags
    def add_metric(
        self,
        name: str,
        value: float,
        timestamp: Optional[int] = None,
        tags: Optional[List] = None,
        **kwargs: Any,
    ) -> None:
        """
        The add_metrics function that will be used by metrics class.

        Parameters
        ----------
        name: str
            Name/Key for the metrics
        value: float
            Value for the metrics
        timestamp: int
            Timestamp in int for the metrics, default = time.time()
        tags: List[str]
            In format like List["tag:value","tag2:value2"]
        args: Any
            extra args will be dropped for compatibility
        kwargs: Any
            extra kwargs will be converted into tags, e.g., add_metrics(sales=sam) -> tags=['sales:sam']

        Examples
        --------
            >>> provider = DataDogProvider()
            >>>
            >>> provider.add_metric(
            >>>     name='coffee_house.order_value',
            >>>     value=12.45,
            >>>     tags=['product:latte', 'order:online'],
            >>>     sales='sam'
            >>> )
        """
        if not isinstance(value, numbers.Real):
            raise MetricValueError(f"{value} is not a valid number")
        if tags is None:
            tags = []
        if not timestamp:
            timestamp = int(time.time())
        for k, w in kwargs.items():
            tags.append(f"{k}:{w}")
        self.metrics.append({"m": name, "v": value, "e": timestamp, "t": tags})

    def serialize(self) -> List:
        output_list: List = []

        for single_metric in self.metrics:
            if self.namespace != DEFAULT_NAMESPACE:
                metric_name = f"{self.namespace}.{single_metric['m']}"
            else:
                metric_name = single_metric["m"]
            output_list.append(
                {
                    "m": metric_name,
                    "v": single_metric["v"],
                    "e": single_metric["e"],
                    "t": single_metric["t"],
                },
            )

        return output_list

    # flush serialized data to output
    def flush(self, metrics: List):
        """

        Parameters
        ----------
        metrics: List[Dict]
        [{
            "m": metric_name,
            "v": value,
            "e": timestamp
            "t": List["tag:value","tag2:value2"]
        }]

        Raises
        -------
        SchemaValidationError
            When metric object fails EMF schema validation
        """
        if len(metrics) == 0:
            raise SchemaValidationError("Must contain at least one metric.")
        # submit through datadog extension
        if lambda_metric and self.flush_to_log is False:
            # use lambda_metric function from datadog package, submit metrics to datadog
            for metric_item in metrics:
                lambda_metric(
                    metric_name=metric_item["m"],
                    value=metric_item["v"],
                    timestamp=metric_item["e"],
                    tags=metric_item["t"],
                )
        else:
            # dd module not found: flush to log, this format can be recognized via datadog log forwarder
            # https://github.com/DataDog/datadog-lambda-python/blob/main/datadog_lambda/metric.py#L77
            for metric_item in metrics:
                print(json.dumps(metric_item, separators=(",", ":")))

    def clear_metrics(self):
        self.metrics = []


class DataDogMetrics(MetricsBase):
    """
    Class for datadog metrics

    Parameters
    ----------
    provider: DataDogProvider
        The datadog provider which will be used to process metrics data

    Example
    -------
    **Creates a few metrics and publish at the end of a function execution**

        >>> from aws_lambda_powertools.metrics.provider import DataDogMetrics, DataDogProvider
        >>>
        >>> dd_provider = DataDogProvider(namespace="Serverlesspresso")
        >>> metrics = DataDogMetrics(provider=dd_provider)
        >>>
        >>> @metrics.log_metrics(capture_cold_start_metric=True, raise_on_empty_metrics=False)
        >>> def lambda_handler(event, context):
        >>>     metrics.add_metric(name="item_sold",value=1,tags=['product:latte', 'order:online'])
    """

    # `log_metrics` and `_add_cold_start_metric` are directly inherited from `MetricsBase`
    def __init__(self, provider: DataDogProvider):
        self.provider = provider
        super().__init__()

    # drop additional kwargs to keep same experience
    def add_metric(
        self,
        name: str,
        value: float,
        timestamp: Optional[int] = None,
        tags: Optional[List] = None,
        *args,
        **kwargs,
    ):
        """
        The add_metrics function that will be used by metrics class.

        Parameters
        ----------
        name: str
            Name/Key for the metrics
        value: float
            Value for the metrics
        timestamp: int
            Timestamp in int for the metrics, default = time.time()
        tags: List[str]
            In format like List["tag:value","tag2:value2"],
        args: Any
            extra args will be dropped
        kwargs: Any
            extra kwargs will be converted into tags, e.g., add_metrics(sales=sam) -> tags=['sales:sam']

        Examples
        --------
            >>> from aws_lambda_powertools.metrics.provider import DataDogMetrics, DataDogProvider
            >>>
            >>> metrics = DataDogMetrics(provider=DataDogProvider())
            >>> metrics.add_metric(
            >>>     name='coffee_house.order_value',
            >>>     value=12.45,
            >>>     tags=['product:latte', 'order:online']
            >>> )
        """
        self.provider.add_metric(name=name, value=value, timestamp=timestamp, tags=tags, **kwargs)

    def flush_metrics(self, raise_on_empty_metrics: bool = False) -> None:
        """
        Manually flushes the metrics. This is normally not necessary,
        unless you're running on other runtimes besides Lambda, where the @log_metrics
        decorator already handles things for you.

        Parameters
        ----------
        raise_on_empty_metrics: bool
            raise exception if no metrics are emitted, by default False
        """
        metrics = self.provider.serialize()
        if not metrics and not raise_on_empty_metrics:
            warnings.warn(
                "No application metrics to publish. The cold-start metric may be published if enabled. "
                "If application metrics should never be empty, consider using 'raise_on_empty_metrics'",
                stacklevel=2,
            )
        else:
            # will raise on empty metrics
            self.provider.flush(metrics)
            self.provider.clear_metrics()
