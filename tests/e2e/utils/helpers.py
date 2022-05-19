import json
from functools import lru_cache
from typing import Any, Optional, Union

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


def trigger_lambda(lambda_arn, client):
    response = client.invoke(FunctionName=lambda_arn, InvocationType="RequestResponse")
    return response


@lru_cache(maxsize=10, typed=False)
@retry(ValueError, delay=1, jitter=1, tries=10)
def get_logs(lambda_function_name: str, log_client: Any, start_time: int, **kwargs):
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
@retry(ValueError, delay=1, jitter=1, tries=10)
def get_metrics(namespace, cw_client, start_date, end_date, metric_name, service_name):
    response = cw_client.get_metric_data(
        MetricDataQueries=[
            {
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "Namespace": namespace,
                        "MetricName": metric_name,
                        "Dimensions": [{"Name": "service", "Value": service_name}],
                    },
                    "Period": 600,
                    "Stat": "Maximum",
                },
                "ReturnData": True,
            },
        ],
        StartTime=start_date,
        EndTime=end_date,
    )
    result = response["MetricDataResults"][0]
    if not result["Values"]:
        raise ValueError("Empty response from Cloudwatch. Repeating...")
    return result


@retry(ValueError, delay=1, jitter=1, tries=10)
def get_traces(lambda_function_name: str, xray_client, start_date, end_date):
    paginator = xray_client.get_paginator("get_trace_summaries")
    response_iterator = paginator.paginate(
        StartTime=start_date,
        EndTime=end_date,
        TimeRangeType="Event",
        Sampling=False,
        FilterExpression=f'service("{lambda_function_name}")',
    )

    traces = [trace["TraceSummaries"][0]["Id"] for trace in response_iterator if trace["TraceSummaries"]]
    if not traces:
        raise ValueError("Empty response from X-RAY. Repeating...")

    trace_details = xray_client.batch_get_traces(
        TraceIds=traces,
    )

    return trace_details
