import json
import secrets
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Union

import boto3
from mypy_boto3_cloudwatch.client import CloudWatchClient
from mypy_boto3_cloudwatch.type_defs import DimensionTypeDef, MetricDataQueryTypeDef, MetricDataResultTypeDef
from mypy_boto3_lambda.client import LambdaClient
from mypy_boto3_lambda.type_defs import InvocationResponseTypeDef
from pydantic import BaseModel
from retry import retry

# Helper methods && Class
from aws_lambda_powertools.metrics import MetricUnit


class Log(BaseModel):
    level: str
    location: str
    message: Union[dict, str]
    timestamp: str
    service: str
    cold_start: Optional[bool]
    function_name: Optional[str]
    function_memory_size: Optional[str]
    function_arn: Optional[str]
    function_request_id: Optional[str]
    xray_trace_id: Optional[str]
    extra_info: Optional[str]


def trigger_lambda(
    lambda_arn: str, payload: Optional[str] = None, client: Optional[LambdaClient] = None
) -> Tuple[InvocationResponseTypeDef, datetime]:
    client = client or boto3.client("lambda")
    payload = payload or ""
    execution_time = datetime.utcnow()
    return client.invoke(FunctionName=lambda_arn, InvocationType="RequestResponse", Payload=payload), execution_time


@lru_cache(maxsize=10, typed=False)
@retry(ValueError, delay=1, jitter=1, tries=20)
def get_logs(lambda_function_name: str, log_client: CloudWatchClient, start_time: int, **kwargs: dict) -> List[Log]:
    response = log_client.filter_log_events(logGroupName=f"/aws/lambda/{lambda_function_name}", startTime=start_time)
    if not response["events"]:
        raise ValueError("Empty response from Cloudwatch Logs. Repeating...")
    filtered_logs = []
    for event in response["events"]:
        try:
            message = Log(**json.loads(event["message"]))
        except json.decoder.JSONDecodeError:
            continue
        filtered_logs.append(message)

    return filtered_logs


@retry(ValueError, delay=2, jitter=1.5, tries=10)
def get_metrics(
    namespace: str,
    start_date: datetime,
    metric_name: str,
    dimensions: Optional[List[DimensionTypeDef]] = None,
    cw_client: Optional[CloudWatchClient] = None,
    end_date: Optional[datetime] = None,
    period: int = 60,
    stat: str = "Sum",
) -> MetricDataResultTypeDef:
    """Fetch CloudWatch Metrics

    It takes into account eventual consistency with up to 10 retries and 1s jitter.

    Parameters
    ----------
    namespace : str
        Metric Namespace
    start_date : datetime
        Start window to fetch metrics
    metric_name : str
        Metric name
    dimensions : Optional[List[DimensionTypeDef]], optional
        List of Metric Dimension, by default None
    cw_client : Optional[CloudWatchClient], optional
        Boto3 CloudWatch low-level client (boto3.client("cloudwatch"), by default None
    end_date : Optional[datetime], optional
        End window to fetch metrics, by default start_date + 2 minutes window
    period : int, optional
        Time period to fetch metrics for, by default 60
    stat : str, optional
        Aggregation function to use when fetching metrics, by default "Sum"

    Returns
    -------
    MetricDataResultTypeDef
        _description_

    Raises
    ------
    ValueError
        When no metric is found within retry window
    """
    cw_client = cw_client or boto3.client("cloudwatch")
    end_date = end_date or start_date + timedelta(minutes=2)

    metric_query = build_metric_query_data(
        namespace=namespace, metric_name=metric_name, period=period, stat=stat, dimensions=dimensions
    )

    response = cw_client.get_metric_data(
        MetricDataQueries=metric_query,
        StartTime=start_date,
        EndTime=end_date or datetime.utcnow(),
    )
    result = response["MetricDataResults"][0]
    if not result["Values"]:
        raise ValueError("Empty response from Cloudwatch. Repeating...")
    return result


# Maintenance: Build a separate module for builders
def build_metric_name() -> str:
    return f"test_metric{build_random_value()}"


def build_service_name() -> str:
    return f"test_service{build_random_value()}"


def build_random_value(nbytes: int = 10) -> str:
    return secrets.token_urlsafe(nbytes).replace("-", "")


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


def build_trace_default_query(function_name: str) -> str:
    return f'service("{function_name}")'
