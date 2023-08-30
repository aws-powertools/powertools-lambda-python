import base64
import sys
from typing import Any, Callable, Dict, Iterator, List, Optional

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class KinesisFirehoseResponseRecordMetadata(DictWrapper):
    """
    Documentation:
    --------------
    - https://docs.aws.amazon.com/firehose/latest/dev/dynamic-partitioning.html
    """

    @property
    def _metadata(self) -> Dict:
        """Optional: metadata associated with this record; present only when Kinesis Stream is source"""
        return self["metadata"]  # could raise KeyError

    @property
    def partition_keys(self) -> Dict[str, str]:
        """Kinesis stream partition key; present only when Kinesis Stream is source"""
        return self._metadata["partitionKeys"]


def KinesisFirehoseResponseRecordMetadataFactory(
    partition_keys: Dict[str, str],
    json_deserializer: Optional[Callable] = None,
) -> KinesisFirehoseResponseRecordMetadata:
    data = {
        "metadata": {
            "partitionKeys": partition_keys,
        },
    }
    return KinesisFirehoseResponseRecordMetadata(data=data, json_deserializer=json_deserializer)


class KinesisFirehoseResponceRecord(DictWrapper):
    """Record in Kinesis Data Firehose event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/firehose/latest/dev/data-transformation.html
    """

    @property
    def record_id(self) -> str:
        """Record ID; uniquely identifies this record within the current batch"""
        return self["recordId"]

    @property
    def result(self) -> Literal["Ok", "Dropped", "ProcessingFailed"]:
        """processing result, supported value: Ok, Dropped, ProcessingFailed"""
        return self["result"]

    @property
    def data(self) -> str:
        """The data blob, base64-encoded"""
        return self["data"]

    @property
    def metadata(self) -> Optional[KinesisFirehoseResponseRecordMetadata]:
        """Optional: metadata associated with this record; present only when Kinesis Stream is source"""
        return KinesisFirehoseResponseRecordMetadata(self._data) if self.get("metadata") else None

    @property
    def data_as_bytes(self) -> bytes:
        """Decoded base64-encoded data as bytes"""
        return base64.b64decode(self.data)

    @property
    def data_as_text(self) -> str:
        """Decoded base64-encoded data as text"""
        return self.data_as_bytes.decode("utf-8")

    @property
    def data_as_json(self) -> Dict:
        """Decoded base64-encoded data loaded to json"""
        if self._json_data is None:
            self._json_data = self._json_deserializer(self.data_as_text)
        return self._json_data


def KinesisFirehoseResponceRecordFactory(
    record_id: str,
    result: Literal["Ok", "Dropped", "ProcessingFailed"],
    data: str,
    metadata: Optional[KinesisFirehoseResponseRecordMetadata] = None,
    json_deserializer: Optional[Callable] = None,
) -> KinesisFirehoseResponceRecord:
    pass_data: Dict[str, Any] = {
        "recordId": record_id,
        "result": result,
        "data": base64.b64encode(data.encode("utf-8")).decode("utf-8"),
    }
    if metadata:
        pass_data["metadata"] = metadata
    return KinesisFirehoseResponceRecord(data=pass_data, json_deserializer=json_deserializer)


class KinesisFirehoseResponce(DictWrapper):
    """Kinesis Data Firehose event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/firehose/latest/dev/data-transformation.html
    """

    @property
    def records(self) -> Iterator[KinesisFirehoseResponceRecord]:
        for record in self["records"]:
            yield KinesisFirehoseResponceRecord(data=record, json_deserializer=self._json_deserializer)


def KinesisFirehoseResponceFactory(
    records: List[KinesisFirehoseResponceRecord],
    json_deserializer: Optional[Callable] = None,
) -> KinesisFirehoseResponce:
    pass_data = {"records": records}
    return KinesisFirehoseResponce(data=pass_data, json_deserializer=json_deserializer)
