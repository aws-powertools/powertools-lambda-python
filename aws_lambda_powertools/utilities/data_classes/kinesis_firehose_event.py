import base64
import json
from typing import Iterator

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class KinesisFirehoseRecordMetadata(DictWrapper):
    @property
    def shard_id(self) -> str:
        """Kinesis stream shard ID; present only when Kinesis Stream is source"""
        return self.get("shardId")

    @property
    def partition_key(self) -> str:
        """Kinesis stream partition key; present only when Kinesis Stream is source"""
        return self.get("partitionKey")

    @property
    def approximate_arrival_timestamp(self) -> str:
        """Kinesis stream approximate arrival ISO timestamp; present only when Kinesis Stream is source"""
        return self.get("approximateArrivalTimestamp")

    @property
    def sequence_number(self) -> str:
        """Kinesis stream sequence number; present only when Kinesis Stream is source"""
        return self.get("sequenceNumber")

    @property
    def subsequence_number(self) -> str:
        """Kinesis stream sub-sequence number; present only when Kinesis Stream is source
        
        Note: this will only be present for Kinesis streams using record aggregation
        """
        return self.get("subsequenceNumber")


class KinesisFirehoseRecord(DictWrapper):
    @property
    def approximate_arrival_timestamp(self) -> float:
        """The approximate time that the record was inserted into the delivery stream"""
        return float(self["approximateArrivalTimestamp"])
    
    @property
    def record_id(self) -> str:
        """Record ID; uniquely identifies this record within the current batch"""
        return self["recordId"]

    @property
    def data(self) -> str:
        """The data blob, base64-encoded"""
        return self["data"]
    
    @property
    def metadata(self) -> KinesisFirehoseRecordMetadata:
        """Optional: metadata associated with this record; present only when Kinesis Stream is source"""
        return KinesisFirehoseRecordMetadata(self.get('kinesisRecordMetadata', {}))

    @property
    def data_as_bytes(self) -> bytes:
        """Decoded base64-encoded data as bytes"""
        return base64.b64decode(self.data)

    @property
    def data_as_text(self) -> str:
        """Decoded base64-encoded data as text"""
        return self.data_as_bytes.decode("utf-8")

    @property
    def data_as_json(self) -> dict:
        """Decoded base64-encoded data loaded to json"""
        if self._json_data is None:
            self._json_data = json.loads(self.data_as_text)
        return self._json_data


class KinesisFirehoseEvent(DictWrapper):
    """Kinesis Data Firehose event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/services-kinesisfirehose.html
    """

    @property
    def invocation_id(self) -> str:
        """Unique ID for for Lambda invocation"""
        return self["invocationId"]

    @property
    def delivery_stream_arn(self) -> str:
        """ARN of the Firehose Data Firehose Delivery Stream"""
        return self["deliveryStreamArn"]

    @property
    def source_kinesis_stream_arn(self) -> str:
        """ARN of the Kinesis Stream; present only when Kinesis Stream is source"""
        return self.get("sourceKinesisStreamArn")

    @property
    def region(self) -> str:
        """AWS region where the event originated eg: us-east-1"""
        return self["region"]

    @property
    def records(self) -> Iterator[KinesisFirehoseRecord]:
        for record in self["records"]:
            yield KinesisFirehoseRecord(record)
