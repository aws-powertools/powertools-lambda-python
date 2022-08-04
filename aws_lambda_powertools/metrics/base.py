import datetime
import json
import logging
import numbers
import os
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ..shared import constants
from ..shared.functions import resolve_env_var_choice
from .exceptions import MetricUnitError, MetricValueError, SchemaValidationError

logger = logging.getLogger(__name__)

MAX_METRICS = 100
MAX_DIMENSIONS = 29


class MetricUnit(Enum):
    Seconds = "Seconds"
    Microseconds = "Microseconds"
    Milliseconds = "Milliseconds"
    Bytes = "Bytes"
    Kilobytes = "Kilobytes"
    Megabytes = "Megabytes"
    Gigabytes = "Gigabytes"
    Terabytes = "Terabytes"
    Bits = "Bits"
    Kilobits = "Kilobits"
    Megabits = "Megabits"
    Gigabits = "Gigabits"
    Terabits = "Terabits"
    Percent = "Percent"
    Count = "Count"
    BytesPerSecond = "Bytes/Second"
    KilobytesPerSecond = "Kilobytes/Second"
    MegabytesPerSecond = "Megabytes/Second"
    GigabytesPerSecond = "Gigabytes/Second"
    TerabytesPerSecond = "Terabytes/Second"
    BitsPerSecond = "Bits/Second"
    KilobitsPerSecond = "Kilobits/Second"
    MegabitsPerSecond = "Megabits/Second"
    GigabitsPerSecond = "Gigabits/Second"
    TerabitsPerSecond = "Terabits/Second"
    CountPerSecond = "Count/Second"


class MetricManager:
    """Base class for metric functionality (namespace, metric, dimension, serialization)

    MetricManager creates metrics asynchronously thanks to CloudWatch Embedded Metric Format (EMF).
    CloudWatch EMF can create up to 100 metrics per EMF object
    and metrics, dimensions, and namespace created via MetricManager
    will adhere to the schema, will be serialized and validated against EMF Schema.

    **Use `aws_lambda_powertools.metrics.metrics.Metrics` or
    `aws_lambda_powertools.metrics.metric.single_metric` to create EMF metrics.**

    Environment variables
    ---------------------
    POWERTOOLS_METRICS_NAMESPACE : str
        metric namespace to be set for all metrics
    POWERTOOLS_SERVICE_NAME : str
        service name used for default dimension

    Raises
    ------
    MetricUnitError
        When metric metric isn't supported by CloudWatch
    MetricValueError
        When metric value isn't a number
    SchemaValidationError
        When metric object fails EMF schema validation
    """

    def __init__(
        self,
        metric_set: Optional[Dict[str, Any]] = None,
        dimension_set: Optional[Dict] = None,
        namespace: Optional[str] = None,
        metadata_set: Optional[Dict[str, Any]] = None,
        service: Optional[str] = None,
    ):
        self.metric_set = metric_set if metric_set is not None else {}
        self.dimension_set = dimension_set if dimension_set is not None else {}
        self.namespace = resolve_env_var_choice(choice=namespace, env=os.getenv(constants.METRICS_NAMESPACE_ENV))
        self.service = resolve_env_var_choice(choice=service, env=os.getenv(constants.SERVICE_NAME_ENV))
        self._metric_units = [unit.value for unit in MetricUnit]
        self._metric_unit_options = list(MetricUnit.__members__)
        self.metadata_set = metadata_set if metadata_set is not None else {}

    def add_metric(self, name: str, unit: Union[MetricUnit, str], value: float) -> None:
        """Adds given metric

        Example
        -------
        **Add given metric using MetricUnit enum**

            metric.add_metric(name="BookingConfirmation", unit=MetricUnit.Count, value=1)

        **Add given metric using plain string as value unit**

            metric.add_metric(name="BookingConfirmation", unit="Count", value=1)

        Parameters
        ----------
        name : str
            Metric name
        unit : Union[MetricUnit, str]
            `aws_lambda_powertools.helper.models.MetricUnit`
        value : float
            Metric value

        Raises
        ------
        MetricUnitError
            When metric unit is not supported by CloudWatch
        """
        if not isinstance(value, numbers.Number):
            raise MetricValueError(f"{value} is not a valid number")

        unit = self.__extract_metric_unit_value(unit=unit)
        metric: Dict = self.metric_set.get(name, defaultdict(list))
        metric["Unit"] = unit
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
        self, metrics: Optional[Dict] = None, dimensions: Optional[Dict] = None, metadata: Optional[Dict] = None
    ) -> Dict:
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
            self.add_dimension(name="service", value=self.service)  # type: ignore[arg-type]

        if len(metrics) == 0:
            raise SchemaValidationError("Must contain at least one metric.")

        if self.namespace is None:
            raise SchemaValidationError("Must contain a metric namespace.")

        logger.debug({"details": "Serializing metrics", "metrics": metrics, "dimensions": dimensions})

        metric_names_and_units: List[Dict[str, str]] = []  # [ { "Name": "metric_name", "Unit": "Count" } ]
        metric_names_and_values: Dict[str, float] = {}  # { "metric_name": 1.0 }

        for metric_name in metrics:
            metric: dict = metrics[metric_name]
            metric_value: int = metric.get("Value", 0)
            metric_unit: str = metric.get("Unit", "")

            metric_names_and_units.append({"Name": metric_name, "Unit": metric_unit})
            metric_names_and_values.update({metric_name: metric_value})

        return {
            "_aws": {
                "Timestamp": int(datetime.datetime.now().timestamp() * 1000),  # epoch
                "CloudWatchMetrics": [
                    {
                        "Namespace": self.namespace,  # "test_namespace"
                        "Dimensions": [list(dimensions.keys())],  # [ "service" ]
                        "Metrics": metric_names_and_units,
                    }
                ],
            },
            **dimensions,  # "service": "test_service"
            **metadata,  # "username": "test"
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
                f"Maximum number of dimensions exceeded ({MAX_DIMENSIONS}): Unable to add dimension {name}."
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

    def __extract_metric_unit_value(self, unit: Union[str, MetricUnit]) -> str:
        """Return metric value from metric unit whether that's str or MetricUnit enum

        Parameters
        ----------
        unit : Union[str, MetricUnit]
            Metric unit

        Returns
        -------
        str
            Metric unit value (e.g. "Seconds", "Count/Second")

        Raises
        ------
        MetricUnitError
            When metric unit is not supported by CloudWatch
        """

        if isinstance(unit, str):
            if unit in self._metric_unit_options:
                unit = MetricUnit[unit].value

            if unit not in self._metric_units:
                raise MetricUnitError(
                    f"Invalid metric unit '{unit}', expected either option: {self._metric_unit_options}"
                )

        if isinstance(unit, MetricUnit):
            unit = unit.value

        return unit
