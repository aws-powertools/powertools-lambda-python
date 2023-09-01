import base64
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterator, List, Optional

from typing_extensions import Literal

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


@dataclass
class KinesisFirehoseResponseRecordMetadata:
    """
    Documentation:
    --------------
    - https://docs.aws.amazon.com/firehose/latest/dev/dynamic-partitioning.html
    """

    partition_keys: Optional[Dict[str, str]]

    def asdict(self) -> Optional[Dict]:
        if self.partition_keys is not None:
            return {"partitionKeys": self.partition_keys}
        return None


@dataclass
class KinesisFirehoseResponseRecord:
    """Record in Kinesis Data Firehose event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/firehose/latest/dev/data-transformation.html
    """

    """Record ID; uniquely identifies this record within the current batch"""
    record_id: str
    """processing result, supported value: Ok, Dropped, ProcessingFailed"""
    result: Literal["Ok", "Dropped", "ProcessingFailed"]
    """data blob, base64-encoded, optional at init. Allows pass in base64-encoded data directly or
            use either function like `data_from_text`, `data_from_json` to populate data"""
    data: Optional[str] = None
    """Optional: metadata associated with this record; present only when Kinesis Stream is source"""
    metadata: Optional[KinesisFirehoseResponseRecordMetadata] = None
    """Json data for caching json.dump result"""
    _json_data: Optional[Any] = None
    json_serializer: Callable = json.dumps
    json_deserializer: Callable = json.loads

    def data_from_byte(self, data: bytes):
        """Populate data field using a byte like data"""
        self.data = base64.b64encode(data).decode("utf-8")

    def data_from_text(self, data: str):
        """Populate data field using a string like data"""
        self.data_from_byte(data.encode("utf-8"))

    def data_from_json(self, data: Any):
        """Populate data field using any structure that could be converted to json"""
        self.data_from_text(data=self.json_serializer(data))

    def asdict(self) -> Dict:
        r: Dict[str, Any] = {
            "recordId": self.record_id,
            "result": self.result,
            "data": self.data,
        }
        if self.metadata:
            r["metadata"] = self.metadata.asdict()
        return r

    @property
    def data_as_bytes(self) -> Optional[bytes]:
        """Decoded base64-encoded data as bytes"""
        if not self.data:
            return None
        return base64.b64decode(self.data)

    @property
    def data_as_text(self) -> Optional[str]:
        """Decoded base64-encoded data as text"""
        if not self.data_as_bytes:
            return None
        return self.data_as_bytes.decode("utf-8")

    @property
    def data_as_json(self) -> Optional[Dict]:
        """Decoded base64-encoded data loaded to json"""
        if not self.data_as_text:
            return None
        if self._json_data is None:
            self._json_data = self.json_deserializer(self.data_as_text)
        return self._json_data


@dataclass
class KinesisFirehoseResponse:
    """Kinesis Data Firehose event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/firehose/latest/dev/data-transformation.html
    """

    records: Optional[List[KinesisFirehoseResponseRecord]] = None

    def add_record(self, record: KinesisFirehoseResponseRecord):
        if self.records:
            self.records.append(record)
        else:
            self.records = [record]

    def asdict(self) -> Dict:
        # make sure return size is less than 6MB
        if not self.records:
            return {}

        return {"records": [r.asdict() for r in self.records]}


class KinesisFirehoseRecordMetadata(DictWrapper):
    @property
    def _metadata(self) -> dict:
        """Optional: metadata associated with this record; present only when Kinesis Stream is source"""
        return self["kinesisRecordMetadata"]  # could raise KeyError

    @property
    def shard_id(self) -> str:
        """Kinesis stream shard ID; present only when Kinesis Stream is source"""
        return self._metadata["shardId"]

    @property
    def partition_key(self) -> str:
        """Kinesis stream partition key; present only when Kinesis Stream is source"""
        return self._metadata["partitionKey"]

    @property
    def approximate_arrival_timestamp(self) -> int:
        """Kinesis stream approximate arrival ISO timestamp; present only when Kinesis Stream is source"""
        return self._metadata["approximateArrivalTimestamp"]

    @property
    def sequence_number(self) -> str:
        """Kinesis stream sequence number; present only when Kinesis Stream is source"""
        return self._metadata["sequenceNumber"]

    @property
    def subsequence_number(self) -> str:
        """Kinesis stream sub-sequence number; present only when Kinesis Stream is source

        Note: this will only be present for Kinesis streams using record aggregation
        """
        return self._metadata["subsequenceNumber"]


class KinesisFirehoseRecord(DictWrapper):
    @property
    def approximate_arrival_timestamp(self) -> int:
        """The approximate time that the record was inserted into the delivery stream"""
        return self["approximateArrivalTimestamp"]

    @property
    def record_id(self) -> str:
        """Record ID; uniquely identifies this record within the current batch"""
        return self["recordId"]

    @property
    def data(self) -> str:
        """The data blob, base64-encoded"""
        return self["data"]

    @property
    def metadata(self) -> Optional[KinesisFirehoseRecordMetadata]:
        """Optional: metadata associated with this record; present only when Kinesis Stream is source"""
        return KinesisFirehoseRecordMetadata(self._data) if self.get("kinesisRecordMetadata") else None

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
            self._json_data = self._json_deserializer(self.data_as_text)
        return self._json_data

    def create_firehose_response_record(
        self,
        result: Literal["Ok", "Dropped", "ProcessingFailed"],
        data: Optional[str] = None,
    ) -> KinesisFirehoseResponseRecord:
        """create a KinesisFirehoseResponseRecord directly using the record_id and given values
        Parameters
        ----------
        result : Literal["Ok", "Dropped", "ProcessingFailed"]
            processing result, supported value: Ok, Dropped, ProcessingFailed
        data : str, optional
            data blob, base64-encoded, optional at init. Allows pass in base64-encoded data directly or
            use either function like `data_from_text`, `data_from_json` to populate data

        """
        return KinesisFirehoseResponseRecord(record_id=self.record_id, result=result, data=data)


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
    def source_kinesis_stream_arn(self) -> Optional[str]:
        """ARN of the Kinesis Stream; present only when Kinesis Stream is source"""
        return self.get("sourceKinesisStreamArn")

    @property
    def region(self) -> str:
        """AWS region where the event originated eg: us-east-1"""
        return self["region"]

    @property
    def records(self) -> Iterator[KinesisFirehoseRecord]:
        for record in self["records"]:
            yield KinesisFirehoseRecord(data=record, json_deserializer=self._json_deserializer)
