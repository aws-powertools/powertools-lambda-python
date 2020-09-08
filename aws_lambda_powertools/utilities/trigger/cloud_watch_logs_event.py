import base64
import json
import zlib
from typing import Dict, List, Optional


class CloudWatchLogsLogEvent(dict):
    @property
    def get_id(self) -> str:
        """The ID property is a unique identifier for every log event."""
        # Note: this name conflicts with existing python builtins
        return self["id"]

    @property
    def timestamp(self) -> int:
        """Get the `timestamp` property"""
        return self["timestamp"]

    @property
    def message(self) -> str:
        """Get the `message` property"""
        return self["message"]

    @property
    def extracted_fields(self) -> Optional[Dict[str, str]]:
        """Get the `extractedFields` property"""
        return self.get("extractedFields")


class CloudWatchLogsDecodedData(dict):
    @property
    def owner(self) -> str:
        """The AWS Account ID of the originating log data."""
        return self["owner"]

    @property
    def log_group(self) -> str:
        """The log group name of the originating log data."""
        return self["logGroup"]

    @property
    def log_stream(self) -> str:
        """The log stream name of the originating log data."""
        return self["logStream"]

    @property
    def subscription_filters(self) -> List[str]:
        """The list of subscription filter names that matched with the originating log data."""
        return self["subscriptionFilters"]

    @property
    def message_type(self) -> str:
        """Data messages will use the "DATA_MESSAGE" type.

        Sometimes CloudWatch Logs may emit Kinesis records with a "CONTROL_MESSAGE" type,
        mainly for checking if the destination is reachable.
        """
        return self["messageType"]

    @property
    def log_events(self) -> List[CloudWatchLogsLogEvent]:
        """The actual log data, represented as an array of log event records.

        The ID property is a unique identifier for every log event.
        """
        return [CloudWatchLogsLogEvent(i) for i in self["logEvents"]]


class CloudWatchLogsEventData(dict):
    @property
    def data(self) -> str:
        """The value of the `data` field is a Base64 encoded ZIP archive."""
        return self["data"]


class CloudWatchLogsEvent(dict):
    """CloudWatch Logs log stream event

    Documentation: https://docs.aws.amazon.com/lambda/latest/dg/services-cloudwatchlogs.html
    """

    @property
    def aws_logs(self) -> CloudWatchLogsEventData:
        return CloudWatchLogsEventData(self["awslogs"])

    def decode_cloud_watch_logs_data(self) -> CloudWatchLogsDecodedData:
        """Gzip and parse json data"""
        payload = base64.b64decode(self.aws_logs.data)
        decoded: dict = json.loads(zlib.decompress(payload, zlib.MAX_WBITS | 32).decode("UTF-8"))
        return CloudWatchLogsDecodedData(decoded)
