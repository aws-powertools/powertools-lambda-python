from __future__ import annotations

import base64
import json
import zlib
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.data_classes.cloud_watch_logs_event import (
    CloudWatchLogsDecodedData,
)
from aws_lambda_powertools.utilities.data_classes.common import DictWrapper

if TYPE_CHECKING:
    from collections.abc import Iterator


class KinesisStreamRecordPayload(DictWrapper):
    @property
    def approximate_arrival_timestamp(self) -> float:
        """The approximate time that the record was inserted into the stream"""
        return float(self["approximateArrivalTimestamp"])

    @property
    def data(self) -> str:
        """The data blob"""
        return self["data"]

    @property
    def kinesis_schema_version(self) -> str:
        """Schema version for the record"""
        return self["kinesisSchemaVersion"]

    @property
    def partition_key(self) -> str:
        """Identifies which shard in the stream the data record is assigned to"""
        return self["partitionKey"]

    @property
    def sequence_number(self) -> str:
        """The unique identifier of the record within its shard"""
        return self["sequenceNumber"]

    def data_as_bytes(self) -> bytes:
        """Decode binary encoded data as bytes"""
        return base64.b64decode(self.data)

    def data_as_text(self) -> str:
        """Decode binary encoded data as text"""
        return self.data_as_bytes().decode("utf-8")

    def data_as_json(self) -> dict:
        """Decode binary encoded data as json"""
        return json.loads(self.data_as_text())

    def data_zlib_compressed_as_json(self) -> dict:
        """Decode binary encoded data as bytes"""
        decompressed = zlib.decompress(self.data_as_bytes(), zlib.MAX_WBITS | 32)
        return json.loads(decompressed)


class KinesisStreamRecord(DictWrapper):
    @property
    def aws_region(self) -> str:
        """AWS region where the event originated eg: us-east-1"""
        return self["awsRegion"]

    @property
    def event_id(self) -> str:
        """A globally unique identifier for the event that was recorded in this stream record."""
        return self["eventID"]

    @property
    def event_name(self) -> str:
        """Event type eg: aws:kinesis:record"""
        return self["eventName"]

    @property
    def event_source(self) -> str:
        """The AWS service from which the Kinesis event originated. For Kinesis, this is aws:kinesis"""
        return self["eventSource"]

    @property
    def event_source_arn(self) -> str:
        """The Amazon Resource Name (ARN) of the event source"""
        return self["eventSourceARN"]

    @property
    def event_version(self) -> str:
        """The eventVersion key value contains a major and minor version in the form <major>.<minor>."""
        return self["eventVersion"]

    @property
    def invoke_identity_arn(self) -> str:
        """The ARN for the identity used to invoke the Lambda Function"""
        return self["invokeIdentityArn"]

    @property
    def kinesis(self) -> KinesisStreamRecordPayload:
        """Underlying Kinesis record associated with the event"""
        return KinesisStreamRecordPayload(self["kinesis"])


class KinesisStreamWindow(DictWrapper):
    @property
    def start(self) -> str:
        """The time window started"""
        return self["start"]

    @property
    def end(self) -> str:
        """The time window will end"""
        return self["end"]


class KinesisStreamEvent(DictWrapper):
    """Kinesis stream event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-kinesis.html
    - https://docs.aws.amazon.com/lambda/latest/dg/services-kinesis-windows.html
    """

    @property
    def records(self) -> Iterator[KinesisStreamRecord]:
        for record in self["Records"]:
            yield KinesisStreamRecord(record)

    @property
    def window(self) -> KinesisStreamWindow | None:
        window = self.get("window")
        if window:
            return KinesisStreamWindow(window)
        return window

    @property
    def state(self) -> dict[str, Any]:
        return self.get("state") or {}

    @property
    def shard_id(self) -> str | None:
        return self.get("shardId")

    @property
    def event_source_arn(self) -> str | None:
        return self.get("eventSourceARN")

    @property
    def is_final_invoke_for_window(self) -> bool | None:
        return self.get("isFinalInvokeForWindow")

    @property
    def is_window_terminated_early(self) -> bool | None:
        return self.get("isWindowTerminatedEarly")


def extract_cloudwatch_logs_from_event(event: KinesisStreamEvent) -> list[CloudWatchLogsDecodedData]:
    return [CloudWatchLogsDecodedData(record.kinesis.data_zlib_compressed_as_json()) for record in event.records]


def extract_cloudwatch_logs_from_record(record: KinesisStreamRecord) -> CloudWatchLogsDecodedData:
    return CloudWatchLogsDecodedData(data=record.kinesis.data_zlib_compressed_as_json())
