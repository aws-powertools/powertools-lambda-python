import json
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional, Union

from mypy_boto3_cloudwatch import type_defs
from mypy_boto3_cloudwatch.client import CloudWatchClient
from mypy_boto3_lambda.client import LambdaClient
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


def trigger_lambda(lambda_arn: str, client: LambdaClient):
    response = client.invoke(FunctionName=lambda_arn, InvocationType="RequestResponse")
    return response


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


@lru_cache(maxsize=10, typed=False)
@retry(ValueError, delay=1, jitter=1, tries=20)
def get_metrics(
    namespace: str,
    cw_client: CloudWatchClient,
    start_date: datetime,
    metric_name: str,
    service_name: str,
    end_date: Optional[datetime] = None,
) -> type_defs.MetricDataResultTypeDef:
    response = cw_client.get_metric_data(
        MetricDataQueries=[
            {
                "Id": "m1",
                "Expression": f'SELECT MAX("{metric_name}") from SCHEMA("{namespace}",service) \
                    where service=\'{service_name}\'',
                "ReturnData": True,
                "Period": 600,
            },
        ],
        StartTime=start_date,
        EndTime=end_date if end_date else datetime.utcnow(),
    )
    result = response["MetricDataResults"][0]
    if not result["Values"]:
        raise ValueError("Empty response from Cloudwatch. Repeating...")
    return result


@retry(ValueError, delay=1, jitter=1, tries=10)
def get_traces(filter_expression: str, xray_client: XRayClient, start_date: datetime, end_date: datetime) -> Dict:
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
