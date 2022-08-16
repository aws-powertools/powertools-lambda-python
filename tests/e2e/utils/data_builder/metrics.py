from typing import Any, Dict, List, Optional

from mypy_boto3_cloudwatch.type_defs import DimensionTypeDef, MetricDataQueryTypeDef

from aws_lambda_powertools.metrics import MetricUnit
from tests.e2e.utils.data_builder.common import build_random_value


def build_metric_query_data(
    namespace: str,
    metric_name: str,
    period: int = 60,
    stat: str = "Sum",
    dimensions: Optional[List[DimensionTypeDef]] = None,
) -> List[MetricDataQueryTypeDef]:
    dimensions = dimensions or []
    data_query: List[MetricDataQueryTypeDef] = [
        {
            "Id": metric_name.lower(),
            "MetricStat": {
                "Metric": {"Namespace": namespace, "MetricName": metric_name},
                "Period": period,
                "Stat": stat,
            },
            "ReturnData": True,
        }
    ]

    if dimensions:
        data_query[0]["MetricStat"]["Metric"]["Dimensions"] = dimensions

    return data_query


def build_add_metric_input(metric_name: str, value: float, unit: str = MetricUnit.Count.value) -> Dict:
    """Create a metric input to be used with Metrics.add_metric()

    Parameters
    ----------
    metric_name : str
        metric name
    value : float
        metric value
    unit : str, optional
        metric unit, by default Count

    Returns
    -------
    Dict
        Metric input
    """
    return {"name": metric_name, "unit": unit, "value": value}


def build_multiple_add_metric_input(
    metric_name: str, value: float, unit: str = MetricUnit.Count.value, quantity: int = 1
) -> List[Dict]:
    """Create list of metrics input to be used with Metrics.add_metric()

    Parameters
    ----------
    metric_name : str
        metric name
    value : float
        metric value
    unit : str, optional
        metric unit, by default Count
    quantity : int, optional
        number of metrics to be created, by default 1

    Returns
    -------
    List[Dict]
        List of metrics
    """
    return [{"name": metric_name, "unit": unit, "value": value} for _ in range(quantity)]


def build_add_dimensions_input(**dimensions) -> List[DimensionTypeDef]:
    """Create dimensions input to be used with either get_metrics or Metrics.add_dimension()

    Parameters
    ----------
    dimensions : str
        key=value pair as dimension

    Returns
    -------
    List[DimensionTypeDef]
        Metric dimension input
    """
    return [{"Name": name, "Value": value} for name, value in dimensions.items()]


def build_put_annotations_input(**annotations: str) -> List[Dict]:
    """Create trace annotations input to be used with Tracer.put_annotation()

    Parameters
    ----------
    annotations : str
        annotations in key=value form

    Returns
    -------
    List[Dict]
        List of put annotations input
    """
    return [{"key": key, "value": value} for key, value in annotations.items()]


def build_put_metadata_input(namespace: Optional[str] = None, **metadata: Any) -> List[Dict]:
    """Create trace metadata input to be used with Tracer.put_metadata()

    All metadata will be under `test` namespace

    Parameters
    ----------
    metadata : Any
        metadata in key=value form

    Returns
    -------
    List[Dict]
        List of put metadata input
    """
    return [{"key": key, "value": value, "namespace": namespace} for key, value in metadata.items()]


def build_metric_name() -> str:
    return f"test_metric{build_random_value()}"
