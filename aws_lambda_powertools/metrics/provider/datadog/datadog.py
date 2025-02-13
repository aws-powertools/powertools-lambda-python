from __future__ import annotations

import json
import logging
import numbers
import os
import re
import time
import warnings
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.metrics.exceptions import MetricValueError, SchemaValidationError
from aws_lambda_powertools.metrics.functions import is_metrics_disabled
from aws_lambda_powertools.metrics.provider import BaseProvider
from aws_lambda_powertools.metrics.provider.datadog.warnings import DatadogDataValidationWarning
from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import resolve_env_var_choice

if TYPE_CHECKING:
    from aws_lambda_powertools.shared.types import AnyCallableT
    from aws_lambda_powertools.utilities.typing import LambdaContext

METRIC_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_.]+$")

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
        metric_set: list | None = None,
        namespace: str | None = None,
        flush_to_log: bool | None = None,
        default_tags: dict[str, Any] | None = None,
    ):
        self.metric_set = metric_set if metric_set is not None else []
        self.namespace = (
            resolve_env_var_choice(choice=namespace, env=os.getenv(constants.METRICS_NAMESPACE_ENV))
            or DEFAULT_NAMESPACE
        )
        self.default_tags = default_tags or {}
        self.flush_to_log = resolve_env_var_choice(choice=flush_to_log, env=os.getenv(constants.DATADOG_FLUSH_TO_LOG))

    #  adding name,value,timestamp,tags
    def add_metric(
        self,
        name: str,
        value: float,
        timestamp: int | None = None,
        **tags,
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
        tags: list[str]
            In format like ["tag:value", "tag2:value2"]

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
        # validating metric name
        if not self._validate_datadog_metric_name(name):
            docs = "https://docs.datadoghq.com/metrics/custom_metrics/#naming-custom-metrics"
            raise SchemaValidationError(
                f"Invalid metric name. Please ensure the metric {name} follows the requirements. \n"
                f"See Datadog documentation here: \n {docs}",
            )

        # validating metric tag
        self._validate_datadog_tags_name(tags)

        if not isinstance(value, numbers.Real):
            raise MetricValueError(f"{value} is not a valid number")

        if not timestamp:
            timestamp = int(time.time())

        logger.debug({"details": "Appending metric", "metrics": name})
        self.metric_set.append({"m": name, "v": value, "e": timestamp, "t": tags})

    def serialize_metric_set(self, metrics: list | None = None) -> list:
        """Serializes metrics

        Example
        -------
        **Serialize metrics into Datadog format**

            metrics = DatadogMetric()
            # ...add metrics, tags, namespace
            ret = metrics.serialize_metric_set()

        Returns
        -------
        list
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

        output_list: list = []

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
                    "t": self._serialize_datadog_tags(metric_tags=single_metric["t"], default_tags=self.default_tags),
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
            logger.debug("Flushing existing metrics")
            metrics = self.serialize_metric_set()
            # submit through datadog extension
            if lambda_metric and not self.flush_to_log:
                # use lambda_metric function from datadog package, submit metrics to datadog
                for metric_item in metrics:  # pragma: no cover
                    lambda_metric(  # pragma: no cover
                        metric_name=metric_item["m"],
                        value=metric_item["v"],
                        timestamp=metric_item["e"],
                        tags=metric_item["t"],
                    )
            elif not is_metrics_disabled():
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
        lambda_handler: AnyCallableT | None = None,
        capture_cold_start_metric: bool = False,
        raise_on_empty_metrics: bool = False,
        **kwargs,
    ):
        """Decorator to serialize and publish metrics at the end of a function execution.

        Be aware that the log_metrics **does call* the decorated function (e.g. lambda_handler).

        Example
        -------
        **Lambda function using tracer and metrics decorators**

            from aws_lambda_powertools import Tracer
            from aws_lambda_powertools.metrics.provider.datadog import DatadogMetrics

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

        default_tags = kwargs.get("default_tags")

        if default_tags:
            self.set_default_tags(**default_tags)

        return super().log_metrics(
            lambda_handler=lambda_handler,
            capture_cold_start_metric=capture_cold_start_metric,
            raise_on_empty_metrics=raise_on_empty_metrics,
            **kwargs,
        )

    def set_default_tags(self, **tags) -> None:
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
        self._validate_datadog_tags_name(tags)
        self.default_tags.update(**tags)

    @staticmethod
    def _serialize_datadog_tags(metric_tags: dict[str, Any], default_tags: dict[str, Any]) -> list[str]:
        """
        Serialize metric tags into a list of formatted strings for Datadog integration.

        This function takes a dictionary of metric-specific tags or default tags.
        It parse these tags and converts them into a list of strings in the format "tag_key:tag_value".

        Parameters
        ----------
        metric_tags: dict[str, Any]
            A dictionary containing metric-specific tags.
        default_tags: dict[str, Any]
            A dictionary containing default tags applicable to all metrics.

        Returns:
        -------
        list[str]
            A list of formatted tag strings, each in the "tag_key:tag_value" format.

        Example:
            >>> metric_tags = {'environment': 'production', 'service': 'web'}
            >>> serialize_datadog_tags(metric_tags, None)
            ['environment:production', 'service:web']
        """

        # We need to create a new dictionary by combining default_tags first,
        # and then metric_tags on top of it. This ensures that the keys from metric_tags take precedence
        # and replace corresponding keys in default_tags.
        tags = {**default_tags, **metric_tags}

        return [f"{tag_key}:{tag_value}" for tag_key, tag_value in tags.items()]

    @staticmethod
    def _validate_datadog_tags_name(tags: dict):
        """
        Validate a metric tag according to specific requirements.

        Metric tags must start with a letter.
        Metric tags must not exceed 200 characters. Fewer than 100 is preferred from a UI perspective.

        More information here: https://docs.datadoghq.com/getting_started/tagging/#define-tags

        Parameters:
        ----------
        tags: dict
            The metric tags to be validated.
        """
        for tag_key, tag_value in tags.items():
            tag = f"{tag_key}:{tag_value}"
            if not tag[0].isalpha() or len(tag) > 200:
                docs = "https://docs.datadoghq.com/getting_started/tagging/#define-tags"
                warnings.warn(
                    f"Invalid tag value. Please ensure the specific tag {tag} follows the requirements. \n"
                    f"May incur data loss for metrics. \n"
                    f"See Datadog documentation here: \n {docs}",
                    DatadogDataValidationWarning,
                    stacklevel=2,
                )

    @staticmethod
    def _validate_datadog_metric_name(metric_name: str) -> bool:
        """
        Validate a metric name according to specific requirements.

        Metric names must start with a letter.
        Metric names must only contain ASCII alphanumerics, underscores, and periods.
        Other characters, including spaces, are converted to underscores.
        Unicode is not supported.
        Metric names must not exceed 200 characters. Fewer than 100 is preferred from a UI perspective.

        More information here: https://docs.datadoghq.com/metrics/custom_metrics/#naming-custom-metrics

        Parameters:
        ----------
        metric_name: str
            The metric name to be validated.

        Returns:
        -------
        bool
            True if the metric name is valid, False otherwise.
        """

        # Check if the metric name starts with a letter
        # Check if the metric name contains more than 200 characters
        # Check if the resulting metric name only contains ASCII alphanumerics, underscores, and periods
        if not metric_name[0].isalpha() or len(metric_name) > 200 or not METRIC_NAME_REGEX.match(metric_name):
            return False

        return True
