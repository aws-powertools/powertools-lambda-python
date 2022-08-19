import json
from datetime import datetime
from typing import List, Optional, Union

import boto3
from mypy_boto3_logs import CloudWatchLogsClient
from pydantic import BaseModel
from retry import retry


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


@retry(ValueError, delay=2, jitter=1.5, tries=10)
def get_logs(
    lambda_function_name: str,
    start_time: datetime,
    log_client: Optional[CloudWatchLogsClient] = None,
    filter_expression: Optional[str] = None,
) -> List[Log]:
    log_client = log_client or boto3.client("logs")
    filter_expression = filter_expression or "message"  # Logger message key

    response = log_client.filter_log_events(
        logGroupName=f"/aws/lambda/{lambda_function_name}",
        startTime=int(start_time.timestamp()),
        filterPattern=filter_expression,
    )

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
