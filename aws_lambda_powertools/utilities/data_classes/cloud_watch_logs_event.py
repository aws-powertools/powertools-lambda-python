from __future__ import annotations

import base64
import zlib

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class CloudWatchLogsLogEvent(DictWrapper):
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
    def extracted_fields(self) -> dict[str, str]:
        """Get the `extractedFields` property"""
        return self.get("extractedFields") or {}


class CloudWatchLogsDecodedData(DictWrapper):
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
    def subscription_filters(self) -> list[str]:
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
    def policy_level(self) -> str | None:
        """The level at which the policy was enforced."""
        return self.get("policyLevel")

    @property
    def log_events(self) -> list[CloudWatchLogsLogEvent]:
        """The actual log data, represented as an array of log event records.

        The ID property is a unique identifier for every log event.
        """
        return [CloudWatchLogsLogEvent(i) for i in self["logEvents"]]


class CloudWatchLogsEvent(DictWrapper):
    """CloudWatch Logs log stream event

    You can use a Lambda function to monitor and analyze logs from an Amazon CloudWatch Logs log stream.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/services-cloudwatchlogs.html
    """

    _decompressed_logs_data = None
    _json_logs_data = None

    @property
    def raw_logs_data(self) -> str:
        """The value of the `data` field is a Base64 encoded ZIP archive."""
        return self["awslogs"]["data"]

    @property
    def decompress_logs_data(self) -> bytes:
        """Decode and decompress log data"""
        if self._decompressed_logs_data is None:
            payload = base64.b64decode(self.raw_logs_data)
            self._decompressed_logs_data = zlib.decompress(payload, zlib.MAX_WBITS | 32)
        return self._decompressed_logs_data

    def parse_logs_data(self) -> CloudWatchLogsDecodedData:
        """Decode, decompress and parse json data as CloudWatchLogsDecodedData"""
        if self._json_logs_data is None:
            self._json_logs_data = self._json_deserializer(self.decompress_logs_data.decode("UTF-8"))

        return CloudWatchLogsDecodedData(self._json_logs_data)
