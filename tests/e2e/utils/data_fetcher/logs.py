import json
from datetime import datetime
from typing import List, Optional, Union

import boto3
from mypy_boto3_logs import CloudWatchLogsClient
from pydantic import BaseModel, Extra
from retry import retry

from aws_lambda_powertools.shared.constants import LOGGER_LAMBDA_CONTEXT_KEYS


class Log(BaseModel, extra=Extra.allow):
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


class LogFetcher:
    def __init__(
        self,
        function_name: str,
        start_time: datetime,
        log_client: Optional[CloudWatchLogsClient] = None,
        filter_expression: Optional[str] = None,
    ) -> None:
        self.function_name = function_name
        self.start_time = int(start_time.timestamp())
        self.log_client = log_client or boto3.client("logs")
        self.filter_expression = filter_expression or "message"  # Logger message key
        self.log_group = f"/aws/lambda/{self.function_name}"
        self.logs: List[Log] = self.get_logs()

    def get_logs(self):
        ret = self.log_client.filter_log_events(
            logGroupName=self.log_group,
            startTime=self.start_time,
            filterPattern=self.filter_expression,
        )

        if not ret["events"]:
            raise ValueError("Empty response from Cloudwatch Logs. Repeating...")

        filtered_logs = []
        for event in ret["events"]:
            try:
                message = Log(**json.loads(event["message"]))
            except json.decoder.JSONDecodeError:
                continue
            filtered_logs.append(message)

        return filtered_logs

    def get_log(self, key: str, value: Optional[any] = None) -> List[Log]:
        logs = []
        for log in self.logs:
            log_value = getattr(log, key, None)
            if value is not None and log_value == value:
                logs.append(log)
            if value is None and getattr(log, key, False):
                logs.append(log)
        return logs

    def get_cold_start_log(self) -> List[Log]:
        return [log for log in self.logs if log.cold_start]

    def have_logger_context_keys(self) -> bool:
        return all(getattr(log, key, False) for log in self.logs for key in LOGGER_LAMBDA_CONTEXT_KEYS)

    def __len__(self) -> int:
        return len(self.logs)


@retry(ValueError, delay=2, jitter=1.5, tries=10)
def get_logs(
    function_name: str,
    start_time: datetime,
    filter_expression: Optional[str] = None,
    log_client: Optional[CloudWatchLogsClient] = None,
) -> LogFetcher:
    return LogFetcher(
        function_name=function_name, start_time=start_time, filter_expression=filter_expression, log_client=log_client
    )
