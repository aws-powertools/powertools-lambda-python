import json
from datetime import datetime
from typing import List, Optional, Union

import boto3
from mypy_boto3_logs import CloudWatchLogsClient
from pydantic import BaseModel, Extra
from retry import retry


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
        minimum_log_entries: int = 1,
    ):
        """Fetch and expose Powertools for AWS Lambda (Python) Logger logs from CloudWatch Logs

        Parameters
        ----------
        function_name : str
            Name of Lambda function to fetch logs for
        start_time : datetime
            Start date range to filter traces
        log_client : Optional[CloudWatchLogsClient], optional
            Amazon CloudWatch Logs Client, by default boto3.client('logs)
        filter_expression : Optional[str], optional
            CloudWatch Logs Filter Pattern expression, by default "message"
        minimum_log_entries: int
            Minimum number of log entries to be retrieved before exhausting retry attempts
        """
        self.function_name = function_name
        self.start_time = int(start_time.timestamp())
        self.log_client = log_client or boto3.client("logs")
        self.filter_expression = filter_expression or "message"  # Logger message key
        self.log_group = f"/aws/lambda/{self.function_name}"
        self.minimum_log_entries = minimum_log_entries
        self.logs: List[Log] = self._get_logs()

    def get_log(self, key: str, value: Optional[any] = None) -> List[Log]:
        """Get logs based on key or key and value

        Parameters
        ----------
        key : str
            Log key name
        value : Optional[any], optional
            Log value, by default None

        Returns
        -------
        List[Log]
            List of Log instances
        """
        logs = []
        for log in self.logs:
            log_value = getattr(log, key, None)
            if value is not None and log_value == value:
                logs.append(log)
            elif value is None and hasattr(log, key):
                logs.append(log)
        return logs

    def get_cold_start_log(self) -> List[Log]:
        """Get logs where cold start was true

        Returns
        -------
        List[Log]
            List of Log instances
        """
        return [log for log in self.logs if log.cold_start]

    def have_keys(self, *keys) -> bool:
        """Whether an arbitrary number of key names exist in each log event

        Returns
        -------
        bool
            Whether keys are present
        """
        return all(hasattr(log, key) for log in self.logs for key in keys)

    def _get_logs(self) -> List[Log]:
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

        if len(filtered_logs) < self.minimum_log_entries:
            raise ValueError(
                f"Number of log entries found doesn't meet minimum required ({self.minimum_log_entries}). Repeating...",
            )

        return filtered_logs

    def __len__(self) -> int:
        return len(self.logs)


@retry(ValueError, delay=2, jitter=1.5, tries=10)
def get_logs(
    function_name: str,
    start_time: datetime,
    minimum_log_entries: int = 1,
    filter_expression: Optional[str] = None,
    log_client: Optional[CloudWatchLogsClient] = None,
) -> LogFetcher:
    """_summary_

    Parameters
    ----------
    function_name : str
        Name of Lambda function to fetch logs for
    start_time : datetime
        Start date range to filter traces
    minimum_log_entries : int
        Minimum number of log entries to be retrieved before exhausting retry attempts
    log_client : Optional[CloudWatchLogsClient], optional
        Amazon CloudWatch Logs Client, by default boto3.client('logs)
    filter_expression : Optional[str], optional
        CloudWatch Logs Filter Pattern expression, by default "message"

    Returns
    -------
    LogFetcher
        LogFetcher instance with logs available as properties and methods
    """
    return LogFetcher(
        function_name=function_name,
        start_time=start_time,
        filter_expression=filter_expression,
        log_client=log_client,
        minimum_log_entries=minimum_log_entries,
    )
