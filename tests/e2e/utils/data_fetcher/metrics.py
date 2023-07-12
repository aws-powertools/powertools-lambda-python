from datetime import datetime, timedelta
from typing import List, Optional

import boto3
from mypy_boto3_cloudwatch import CloudWatchClient
from mypy_boto3_cloudwatch.type_defs import DimensionTypeDef
from retry import retry

from tests.e2e.utils.data_builder import build_metric_query_data


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
) -> List[float]:
    """Fetch CloudWatch Metrics

    It takes into account eventual consistency with up to 10 retries and 1.5s jitter.

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
    List[float]
        List with metric values found

    Raises
    ------
    ValueError
        When no metric is found within retry window
    """
    cw_client = cw_client or boto3.client("cloudwatch")
    end_date = end_date or start_date + timedelta(minutes=2)

    metric_query = build_metric_query_data(
        namespace=namespace,
        metric_name=metric_name,
        period=period,
        stat=stat,
        dimensions=dimensions,
    )

    response = cw_client.get_metric_data(
        MetricDataQueries=metric_query,
        StartTime=start_date,
        EndTime=end_date or datetime.utcnow(),
    )
    result = response["MetricDataResults"][0]["Values"]
    if not result:
        raise ValueError("Empty response from Cloudwatch. Repeating...")
    return result
