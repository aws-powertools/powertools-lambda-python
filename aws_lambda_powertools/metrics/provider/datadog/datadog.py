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
from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import resolve_env_var_choice
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = logging.getLogger(__name__)

# Check if using datadog layer
try:
    from datadog_lambda.metric import lambda_metric  # type: ignore
except ImportError:  # pragma: no cover
    lambda_metric = None  # pragma: no cover

DEFAULT_NAMESPACE = "default"


class DatadogProvider(BaseProvider):
    """
    DatadogProvider creates metrics asynchronously via Datadog extension or exporter.

    **Use `aws_lambda_powertools.DatadogMetrics` to create and metrics to Datadog.**

    Environment variables
    ---------------------
    POWERTOOLS_METRICS_NAMESPACE : str
        metric namespace to be set for all metrics

    Raises
    ------
    MetricValueError
        When metric value isn't a number
    SchemaValidationError
        When metric object fails EMF schema validation
    """

    def __init__(
        self,
        metric_set: List | None = None,
        namespace: str | None = None,
        flush_to_log: bool | None = None,
        default_tags: List | None = None,
    ):
        self.metric_set = metric_set if metric_set is not None else []
        self.namespace = resolve_env_var_choice(choice=namespace, env=os.getenv(constants.METRICS_NAMESPACE_ENV))
        if self.namespace is None:
            self.namespace = DEFAULT_NAMESPACE
        self.default_tags = default_tags or []
        self.flush_to_log = resolve_env_var_choice(choice=flush_to_log, env=os.getenv(constants.DATADOG_FLUSH_TO_LOG))

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

        for tag_key, tag_value in kwargs.items():
            tags.append(f"{tag_key}:{tag_value}")

        self.metric_set.append({"m": name, "v": value, "e": timestamp, "t": tags})

    def serialize_metric_set(self, metrics: List | None = None) -> List:
        """Serializes metrics

        Example
        -------
        **Serialize metrics into Datadog format**

            metrics = DatadogMetric()
            # ...add metrics, tags, namespace
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
                    "t": single_metric["t"] or list(self.default_tags),
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
                for metric_item in metrics:  # pragma: no cover
                    lambda_metric(  # pragma: no cover
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

            from aws_lambda_powertools import DatadogMetrics, Tracer

            metrics = DatadogMetrics(namespace="powertools")
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

        default_dimensions = kwargs.get("default_tags")

        if default_dimensions:
            self.set_default_tags(**default_dimensions)

        return super().log_metrics(
            lambda_handler=lambda_handler,
            capture_cold_start_metric=capture_cold_start_metric,
            raise_on_empty_metrics=raise_on_empty_metrics,
            **kwargs,
        )

    def set_default_tags(self, **kwargs) -> None:
        """Persist tags across Lambda invocations

        Parameters
        ----------
        tags : **kwargs
            tags as key=value

        Example
        -------
        **Sets some default dimensions that will always be present across metrics and invocations**

            from aws_lambda_powertools import Metrics

            metrics = Metrics(namespace="ServerlessAirline", service="payment")
            metrics.set_default_tags(environment="demo", another="one")

            @metrics.log_metrics()
            def lambda_handler():
                return True
        """
        for tag_key, tag_value in kwargs.items():
            self.default_tags.append(f"{tag_key}:{tag_value}")
