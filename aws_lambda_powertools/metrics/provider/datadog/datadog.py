from __future__ import annotations

import json
import logging
import numbers
import os
import time
import warnings
from typing import Any, Callable, Dict, List, Optional

from aws_lambda_powertools.metrics.exceptions import MetricValueError, SchemaValidationError
from aws_lambda_powertools.metrics.provider import BaseProvider
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = logging.getLogger(__name__)

# Check if using datadog layer
try:
    from datadog_lambda.metric import lambda_metric  # type: ignore
except ImportError:
    lambda_metric = None

DEFAULT_NAMESPACE = "default"


class DatadogProvider(BaseProvider):
    """
    Class for datadog provider. This Class should only be used inside DatadogMetrics
    all datadog metric data will be stored as
    {
        "m": metric_name,
        "v": value,
        "e": timestamp
        "t": List["tag:value","tag2:value2"]
    }
    see https://github.com/Datadog/datadog-lambda-python/blob/main/datadog_lambda/metric.py#L77

    Examples
    --------

    """

    def __init__(self, metric_set: List | None = None, namespace: str = DEFAULT_NAMESPACE, flush_to_log: bool = False):
        """

        Parameters
        ----------
        namespace: str
            For datadog, namespace will be appended in front of the metrics name in metrics exported.
            (namespace.metrics_name)
        flush_to_log: bool
            Flush datadog metrics to log (collect with log forwarder) rather than using datadog extension
        """
        self.metric_set = metric_set if metric_set is not None else []
        self.namespace: str = namespace
        # either is true then flush to log
        self.flush_to_log = (os.environ.get("DD_FLUSH_TO_LOG", "").lower() == "true") or flush_to_log

    #  adding name,value,timestamp,tags
    def add_metric(
        self,
        name: str,
        value: float,
        timestamp: int | None = None,
        tags: List | None = None,
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
            >>> provider = DatadogProvider()
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
        self.metric_set.append({"m": name, "v": value, "e": timestamp, "t": tags})

    def serialize_metric_set(self, metrics: List | None = None) -> List:
        """Serializes metrics

        Example
        -------
        **Serialize metrics into Datadog format**

            metrics = DatadogMetric()
            # ...add metrics, dimensions, namespace
            ret = metrics.serialize_metric_set()

        Returns
        -------
        List
            Serialized metrics following Datadog specification

        Raises
        ------
        SchemaValidationError
            Raised when serialization fail schema validation
        """

        if metrics is None:  # pragma: no cover
            metrics = self.metric_set

        if len(metrics) == 0:
            raise SchemaValidationError("Must contain at least one metric.")

        output_list: List = []

        logger.debug({"details": "Serializing metrics", "metrics": metrics})

        for single_metric in metrics:
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
    def flush_metrics(self, raise_on_empty_metrics: bool = False) -> None:
        """Manually flushes the metrics. This is normally not necessary,
        unless you're running on other runtimes besides Lambda, where the @log_metrics
        decorator already handles things for you.

        Parameters
        ----------
        raise_on_empty_metrics : bool, optional
            raise exception if no metrics are emitted, by default False
        """
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
        if not raise_on_empty_metrics and len(self.metric_set) == 0:
            warnings.warn(
                "No application metrics to publish. The cold-start metric may be published if enabled. "
                "If application metrics should never be empty, consider using 'raise_on_empty_metrics'",
                stacklevel=2,
            )

        else:
            metrics = self.serialize_metric_set()
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
                # https://github.com/Datadog/datadog-lambda-python/blob/main/datadog_lambda/metric.py#L77
                for metric_item in metrics:
                    print(json.dumps(metric_item, separators=(",", ":")))

        self.clear_metrics()

    def clear_metrics(self):
        logger.debug("Clearing out existing metric set from memory")
        self.metric_set.clear()

    def add_cold_start_metric(self, context: LambdaContext) -> None:
        """Add cold start metric and function_name dimension

        Parameters
        ----------
        context : Any
            Lambda context
        """
        logger.debug("Adding cold start metric and function_name tagging")
        self.add_metric(name="ColdStart", value=1, function_name=context.function_name)

    def log_metrics(
        self,
        lambda_handler: Callable[[Dict, Any], Any] | Optional[Callable[[Dict, Any, Optional[Dict]], Any]] = None,
        capture_cold_start_metric: bool = False,
        raise_on_empty_metrics: bool = False,
        **kwargs,
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
            lambda function handler, by default None
        capture_cold_start_metric : bool, optional
            captures cold start metric, by default False
        raise_on_empty_metrics : bool, optional
            raise exception if no metrics are emitted, by default False
        **kwargs

        Raises
        ------
        e
            Propagate error received
        """

        return super().log_metrics(
            lambda_handler=lambda_handler,
            capture_cold_start_metric=capture_cold_start_metric,
            raise_on_empty_metrics=raise_on_empty_metrics,
            **kwargs,
        )
