import json
import secrets
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional, Tuple, Union

import boto3
from mypy_boto3_cloudwatch.client import CloudWatchClient
from mypy_boto3_cloudwatch.type_defs import DimensionTypeDef, MetricDataQueryTypeDef, MetricDataResultTypeDef
from mypy_boto3_lambda.client import LambdaClient
from mypy_boto3_lambda.type_defs import InvocationResponseTypeDef
from mypy_boto3_xray.client import XRayClient
from pydantic import BaseModel
from retry import retry


# Helper methods && Class
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


class TraceSegment(BaseModel):
    name: str
    metadata: Dict = {}
    annotations: Dict = {}


def trigger_lambda(
    lambda_arn: str, payload: str, client: Optional[LambdaClient] = None
) -> Tuple[InvocationResponseTypeDef, datetime]:
    client = client or boto3.client("lambda")
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


@retry(ValueError, delay=1, jitter=1, tries=10)
def get_metrics(
    namespace: str,
    start_date: datetime,
    metric_name: str,
    service_name: str,
    cw_client: Optional[CloudWatchClient] = None,
    end_date: Optional[datetime] = None,
    period: int = 60,
    stat: str = "Sum",
) -> MetricDataResultTypeDef:
    cw_client = cw_client or boto3.client("cloudwatch")
    metric_query = build_metric_query_data(
        namespace=namespace, metric_name=metric_name, service_name=service_name, period=period, stat=stat
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


@retry(ValueError, delay=1, jitter=1, tries=10)
def get_traces(
    filter_expression: str, start_date: datetime, end_date: datetime, xray_client: Optional[XRayClient] = None
) -> Dict:
    xray_client = xray_client or boto3.client("xray")
    paginator = xray_client.get_paginator("get_trace_summaries")
    response_iterator = paginator.paginate(
        StartTime=start_date,
        EndTime=end_date,
        TimeRangeType="Event",
        Sampling=False,
        FilterExpression=filter_expression,
    )

    traces = [trace["TraceSummaries"][0]["Id"] for trace in response_iterator if trace["TraceSummaries"]]
    if not traces:
        raise ValueError("Empty response from X-RAY. Repeating...")

    trace_details = xray_client.batch_get_traces(
        TraceIds=traces,
    )

    return trace_details


def find_trace_additional_info(trace: Dict) -> List[TraceSegment]:
    """Find all trace annotations and metadata and return them to the caller"""
    info = []
    for segment in trace["Traces"][0]["Segments"]:
        document = json.loads(segment["Document"])
        if document["origin"] == "AWS::Lambda::Function":
            for subsegment in document["subsegments"]:
                if subsegment["name"] == "Invocation":
                    find_meta(segment=subsegment, result=info)
    return info


def find_meta(segment: dict, result: List):
    for x_subsegment in segment["subsegments"]:
        result.append(
            TraceSegment(
                name=x_subsegment["name"],
                metadata=x_subsegment.get("metadata", {}),
                annotations=x_subsegment.get("annotations", {}),
            )
        )
        if x_subsegment.get("subsegments"):
            find_meta(segment=x_subsegment, result=result)


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
    service_name: str,
    period: int = 60,
    stat: str = "Sum",
    dimensions: Optional[DimensionTypeDef] = None,
) -> List[MetricDataQueryTypeDef]:
    metric_dimensions: List[DimensionTypeDef] = [{"Name": "service", "Value": service_name}]
    if dimensions is not None:
        metric_dimensions.append(dimensions)

    return [
        {
            "Id": metric_name,
            "MetricStat": {
                "Metric": {"Namespace": namespace, "MetricName": metric_name, "Dimensions": metric_dimensions},
                "Period": period,
                "Stat": stat,
            },
            "ReturnData": True,
        }
    ]
