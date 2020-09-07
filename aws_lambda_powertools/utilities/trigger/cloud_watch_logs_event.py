import base64
import json
import zlib
from typing import Dict, List, Optional


class CloudWatchLogsLogEvent(dict):
    @property
    def id(self) -> str:  # noqa: A003
        return self["id"]

    @property
    def timestamp(self) -> int:
        return self["timestamp"]

    @property
    def message(self) -> str:
        return self["message"]

    @property
    def extracted_fields(self) -> Optional[Dict[str, str]]:
        return self.get("extractedFields")


class CloudWatchLogsDecodedData(dict):
    @property
    def owner(self) -> str:
        return self["owner"]

    @property
    def log_group(self) -> str:
        return self["logGroup"]

    @property
    def log_stream(self) -> str:
        return self["logStream"]

    @property
    def subscription_filters(self) -> List[str]:
        return self["subscriptionFilters"]

    @property
    def message_type(self) -> str:
        return self["messageType"]

    @property
    def log_events(self) -> List[CloudWatchLogsLogEvent]:
        return [CloudWatchLogsLogEvent(i) for i in self["logEvents"]]


class CloudWatchLogsEventData(dict):
    @property
    def data(self) -> str:
        return self["data"]


class CloudWatchLogsEvent(dict):
    @property
    def aws_logs(self) -> CloudWatchLogsEventData:
        return CloudWatchLogsEventData(self["awslogs"])

    def cloud_watch_logs_decoded_data(self) -> CloudWatchLogsDecodedData:
        """Gzip and parse data"""
        payload = base64.b64decode(self.aws_logs.data)
        decoded: dict = json.loads(zlib.decompress(payload, zlib.MAX_WBITS | 32).decode("UTF-8"))
        return CloudWatchLogsDecodedData(decoded)
