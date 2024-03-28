from __future__ import annotations

import datetime
import json
import logging
import numbers
import os
import warnings
from collections import defaultdict
from typing import Any, Dict, List

from aws_lambda_powertools.metrics.base import single_metric
from aws_lambda_powertools.metrics.exceptions import MetricValueError, SchemaValidationError
from aws_lambda_powertools.metrics.functions import (
    convert_timestamp_to_emf_format,
    extract_cloudwatch_metric_resolution_value,
    extract_cloudwatch_metric_unit_value,
    validate_emf_timestamp,
)
from aws_lambda_powertools.metrics.provider.base import BaseProvider
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.constants import MAX_DIMENSIONS, MAX_METRICS
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.metric_properties import MetricResolution, MetricUnit
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.types import CloudWatchEMFOutput
from aws_lambda_powertools.metrics.types import MetricNameUnitResolution
from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import resolve_env_var_choice
from aws_lambda_powertools.shared.types import AnyCallableT
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = logging.getLogger(__name__)


class AmazonCloudWatchEMFProvider(BaseProvider):
    """
    AmazonCloudWatchEMFProvider creates metrics asynchronously via CloudWatch Embedded Metric Format (EMF).

    CloudWatch EMF can create up to 100 metrics per EMF object
    and metrics, dimensions, and namespace created via AmazonCloudWatchEMFProvider
    will adhere to the schema, will be serialized and validated against EMF Schema.

    **Use `aws_lambda_powertools.Metrics` or
    `aws_lambda_powertools.single_metric` to create EMF metrics.**

    Environment variables
    ---------------------
    POWERTOOLS_METRICS_NAMESPACE : str
        metric namespace to be set for all metrics
    POWERTOOLS_SERVICE_NAME : str
        service name used for default dimension

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

    def __init__(
        self,
        metric_set: Dict[str, Any] | None = None,
        dimension_set: Dict | None = None,
        namespace: str | None = None,
        metadata_set: Dict[str, Any] | None = None,
        service: str | None = None,
        default_dimensions: Dict[str, Any] | None = None,
    ):
        self.metric_set = metric_set if metric_set is not None else {}
        self.dimension_set = dimension_set if dimension_set is not None else {}
        self.default_dimensions = default_dimensions or {}
        self.namespace = resolve_env_var_choice(choice=namespace, env=os.getenv(constants.METRICS_NAMESPACE_ENV))
        self.service = resolve_env_var_choice(choice=service, env=os.getenv(constants.SERVICE_NAME_ENV))
        self.metadata_set = metadata_set if metadata_set is not None else {}
        self.timestamp: int | None = None

        self._metric_units = [unit.value for unit in MetricUnit]
        self._metric_unit_valid_options = list(MetricUnit.__members__)
        self._metric_resolutions = [resolution.value for resolution in MetricResolution]

        self.dimension_set.update(**self.default_dimensions)

    def add_metric(
        self,
        name: str,
        unit: MetricUnit | str,
        value: float,
        resolution: MetricResolution | int = 60,
    ) -> None:
        """Adds given metric

        Example
        -------
        **Add given metric using MetricUnit enum**

            metric.add_metric(name="BookingConfirmation", unit=MetricUnit.Count, value=1)

        **Add given metric using plain string as value unit**

            metric.add_metric(name="BookingConfirmation", unit="Count", value=1)

        **Add given metric with MetricResolution non default value**

            metric.add_metric(name="BookingConfirmation", unit="Count", value=1, resolution=MetricResolution.High)

        Parameters
        ----------
        name : str
            Metric name
        unit : Union[MetricUnit, str]
            `aws_lambda_powertools.helper.models.MetricUnit`
        value : float
            Metric value
        resolution : Union[MetricResolution, int]
            `aws_lambda_powertools.helper.models.MetricResolution`

        Raises
        ------
        MetricUnitError
            When metric unit is not supported by CloudWatch
        MetricResolutionError
            When metric resolution is not supported by CloudWatch
        """
        if not isinstance(value, numbers.Number):
            raise MetricValueError(f"{value} is not a valid number")

        unit = extract_cloudwatch_metric_unit_value(
            metric_units=self._metric_units,
            metric_valid_options=self._metric_unit_valid_options,
            unit=unit,
        )
        resolution = extract_cloudwatch_metric_resolution_value(
            metric_resolutions=self._metric_resolutions,
            resolution=resolution,
        )
        metric: Dict = self.metric_set.get(name, defaultdict(list))
        metric["Unit"] = unit
        metric["StorageResolution"] = resolution
        metric["Value"].append(float(value))
        logger.debug(f"Adding metric: {name} with {metric}")
        self.metric_set[name] = metric

        if len(self.metric_set) == MAX_METRICS or len(metric["Value"]) == MAX_METRICS:
            logger.debug(f"Exceeded maximum of {MAX_METRICS} metrics - Publishing existing metric set")
            metrics = self.serialize_metric_set()
            print(json.dumps(metrics))

            # clear metric set only as opposed to metrics and dimensions set
            # since we could have more than 100 metrics
            self.metric_set.clear()

    def serialize_metric_set(
        self,
        metrics: Dict | None = None,
        dimensions: Dict | None = None,
        metadata: Dict | None = None,
    ) -> CloudWatchEMFOutput:
        """Serializes metric and dimensions set

        Parameters
        ----------
        metrics : Dict, optional
            Dictionary of metrics to serialize, by default None
        dimensions : Dict, optional
            Dictionary of dimensions to serialize, by default None
        metadata: Dict, optional
            Dictionary of metadata to serialize, by default None

        Example
        -------
        **Serialize metrics into EMF format**

            metrics = MetricManager()
            # ...add metrics, dimensions, namespace
            ret = metrics.serialize_metric_set()

        Returns
        -------
        Dict
            Serialized metrics following EMF specification

        Raises
        ------
        SchemaValidationError
            Raised when serialization fail schema validation
        """
        if metrics is None:  # pragma: no cover
            metrics = self.metric_set

        if dimensions is None:  # pragma: no cover
            dimensions = self.dimension_set

        if metadata is None:  # pragma: no cover
            metadata = self.metadata_set

        if self.service and not self.dimension_set.get("service"):
            # self.service won't be a float
            self.add_dimension(name="service", value=self.service)

        if len(metrics) == 0:
            raise SchemaValidationError("Must contain at least one metric.")

        if self.namespace is None:
            raise SchemaValidationError("Must contain a metric namespace.")

        logger.debug({"details": "Serializing metrics", "metrics": metrics, "dimensions": dimensions})

        # For standard resolution metrics, don't add StorageResolution field to avoid unnecessary ingestion of data into cloudwatch # noqa E501
        # Example: [ { "Name": "metric_name", "Unit": "Count"} ] # noqa ERA001
        #
        # In case using high-resolution metrics, add StorageResolution field
        # Example: [ { "Name": "metric_name", "Unit": "Count", "StorageResolution": 1 } ] # noqa ERA001
        metric_definition: List[MetricNameUnitResolution] = []
        metric_names_and_values: Dict[str, float] = {}  # { "metric_name": 1.0 }

        for metric_name in metrics:
            metric: dict = metrics[metric_name]
            metric_value: int = metric.get("Value", 0)
            metric_unit: str = metric.get("Unit", "")
            metric_resolution: int = metric.get("StorageResolution", 60)

            metric_definition_data: MetricNameUnitResolution = {"Name": metric_name, "Unit": metric_unit}

            # high-resolution metrics
            if metric_resolution == 1:
                metric_definition_data["StorageResolution"] = metric_resolution

            metric_definition.append(metric_definition_data)

            metric_names_and_values.update({metric_name: metric_value})

        return {
            "_aws": {
                "Timestamp": self.timestamp or int(datetime.datetime.now().timestamp() * 1000),  # epoch
                "CloudWatchMetrics": [
                    {
                        "Namespace": self.namespace,  # "test_namespace"
                        "Dimensions": [list(dimensions.keys())],  # [ "service" ]
                        "Metrics": metric_definition,
                    },
                ],
            },
            # NOTE: Mypy doesn't recognize splats '** syntax' in TypedDict
            **dimensions,  # "service": "test_service"
            **metadata,  # type: ignore[typeddict-item] # "username": "test"
            **metric_names_and_values,  # "single_metric": 1.0
        }

    def add_dimension(self, name: str, value: str) -> None:
        """Adds given dimension to all metrics

        Example
        -------
        **Add a metric dimensions**

            metric.add_dimension(name="operation", value="confirm_booking")

        Parameters
        ----------
        name : str
            Dimension name
        value : str
            Dimension value
        """
        logger.debug(f"Adding dimension: {name}:{value}")
        if len(self.dimension_set) == MAX_DIMENSIONS:
            raise SchemaValidationError(
                f"Maximum number of dimensions exceeded ({MAX_DIMENSIONS}): Unable to add dimension {name}.",
            )
        # Cast value to str according to EMF spec
        # Majority of values are expected to be string already, so
        # checking before casting improves performance in most cases
        self.dimension_set[name] = value if isinstance(value, str) else str(value)

    def add_metadata(self, key: str, value: Any) -> None:
        """Adds high cardinal metadata for metrics object

        This will not be available during metrics visualization.
        Instead, this will be searchable through logs.

        If you're looking to add metadata to filter metrics, then
        use add_dimensions method.

        Example
        -------
        **Add metrics metadata**

            metric.add_metadata(key="booking_id", value="booking_id")

        Parameters
        ----------
        key : str
            Metadata key
        value : any
            Metadata value
        """
        logger.debug(f"Adding metadata: {key}:{value}")

        # Cast key to str according to EMF spec
        # Majority of keys are expected to be string already, so
        # checking before casting improves performance in most cases
        if isinstance(key, str):
            self.metadata_set[key] = value
        else:
            self.metadata_set[str(key)] = value

    def set_timestamp(self, timestamp: int | datetime.datetime):
        """
        Set the timestamp for the metric.

        Parameters:
        -----------
        timestamp: int | datetime.datetime
            The timestamp to create the metric.
            If an integer is provided, it is assumed to be the epoch time in milliseconds.
            If a datetime object is provided, it will be converted to epoch time in milliseconds.
        """
        # The timestamp must be a Datetime object or an integer representing an epoch time.
        # This should not exceed 14 days in the past or be more than 2 hours in the future.
        # Any metrics failing to meet this criteria will be skipped by Amazon CloudWatch.
        # See: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html
        # See: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch-Logs-Monitoring-CloudWatch-Metrics.html
        if not validate_emf_timestamp(timestamp):
            warnings.warn(
                "This metric doesn't meet the requirements and will be skipped by Amazon CloudWatch. "
                "Ensure the timestamp is within 14 days past or 2 hours future.",
                stacklevel=2,
            )

        self.timestamp = convert_timestamp_to_emf_format(timestamp)

    def clear_metrics(self) -> None:
        logger.debug("Clearing out existing metric set from memory")
        self.metric_set.clear()
        self.dimension_set.clear()
        self.metadata_set.clear()
        self.set_default_dimensions(**self.default_dimensions)

    def flush_metrics(self, raise_on_empty_metrics: bool = False) -> None:
        """Manually flushes the metrics. This is normally not necessary,
        unless you're running on other runtimes besides Lambda, where the @log_metrics
        decorator already handles things for you.

        Parameters
        ----------
        raise_on_empty_metrics : bool, optional
            raise exception if no metrics are emitted, by default False
        """
        if not raise_on_empty_metrics and not self.metric_set:
            warnings.warn(
                "No application metrics to publish. The cold-start metric may be published if enabled. "
                "If application metrics should never be empty, consider using 'raise_on_empty_metrics'",
                stacklevel=2,
            )
        else:
            logger.debug("Flushing existing metrics")
            metrics = self.serialize_metric_set()
            print(json.dumps(metrics, separators=(",", ":")))
            self.clear_metrics()

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

        default_dimensions = kwargs.get("default_dimensions")

        if default_dimensions:
            self.set_default_dimensions(**default_dimensions)

        return super().log_metrics(
            lambda_handler=lambda_handler,
            capture_cold_start_metric=capture_cold_start_metric,
            raise_on_empty_metrics=raise_on_empty_metrics,
            **kwargs,
        )

    def add_cold_start_metric(self, context: LambdaContext) -> None:
        """Add cold start metric and function_name dimension

        Parameters
        ----------
        context : Any
            Lambda context
        """
        logger.debug("Adding cold start metric and function_name dimension")
        with single_metric(name="ColdStart", unit=MetricUnit.Count, value=1, namespace=self.namespace) as metric:
            metric.add_dimension(name="function_name", value=context.function_name)
            if self.service:
                metric.add_dimension(name="service", value=str(self.service))

    def set_default_dimensions(self, **dimensions) -> None:
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
