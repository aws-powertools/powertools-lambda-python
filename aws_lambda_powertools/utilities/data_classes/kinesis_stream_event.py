import base64
import json
from typing import Iterator

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class KinesisStreamRecordPayload(DictWrapper):
    @property
    def approximate_arrival_timestamp(self) -> float:
        """The approximate time that the record was inserted into the stream"""
        return float(self["kinesis"]["approximateArrivalTimestamp"])

    @property
    def data(self) -> str:
        """The data blob"""
        return self["kinesis"]["data"]

    @property
    def kinesis_schema_version(self) -> str:
        """Schema version for the record"""
        return self["kinesis"]["kinesisSchemaVersion"]

    @property
    def partition_key(self) -> str:
        """Identifies which shard in the stream the data record is assigned to"""
        return self["kinesis"]["partitionKey"]

    @property
    def sequence_number(self) -> str:
        """The unique identifier of the record within its shard"""
        return self["kinesis"]["sequenceNumber"]

    def data_as_bytes(self) -> bytes:
        """Decode binary encoded data as bytes"""
        return base64.b64decode(self.data)

    def data_as_text(self) -> str:
        """Decode binary encoded data as text"""
        return self.data_as_bytes().decode("utf-8")

    def data_as_json(self) -> dict:
        """Decode binary encoded data as json"""
        return json.loads(self.data_as_text())


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
        return KinesisStreamRecordPayload(self._data)


class KinesisStreamEvent(DictWrapper):
    """Kinesis stream event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-kinesis.html
    """

    @property
    def records(self) -> Iterator[KinesisStreamRecord]:
        for record in self["Records"]:
            yield KinesisStreamRecord(record)
