import json
import zlib
from typing import Dict, List, Type, Union

from pydantic import BaseModel, validator

from aws_lambda_powertools.shared.functions import base64_decode
from aws_lambda_powertools.utilities.parser.models.cloudwatch import (
    CloudWatchLogsDecode,
)
from aws_lambda_powertools.utilities.parser.types import Literal


class KinesisDataStreamRecordPayload(BaseModel):
    kinesisSchemaVersion: str
    partitionKey: str
    sequenceNumber: str
    data: Union[bytes, Type[BaseModel], BaseModel]  # base64 encoded str is parsed into bytes
    approximateArrivalTimestamp: float

    @validator("data", pre=True, allow_reuse=True)
    def data_base64_decode(cls, value):
        return base64_decode(value)


class KinesisDataStreamRecord(BaseModel):
    eventSource: Literal["aws:kinesis"]
    eventVersion: str
    eventID: str
    eventName: Literal["aws:kinesis:record"]
    invokeIdentityArn: str
    awsRegion: str
    eventSourceARN: str
    kinesis: KinesisDataStreamRecordPayload

    def decompress_zlib_record_data_as_json(self) -> Dict:
        """Decompress Kinesis Record bytes data zlib compressed to JSON"""
        if not isinstance(self.kinesis.data, bytes):
            raise ValueError("We can only decompress bytes data, not custom models.")

        return json.loads(zlib.decompress(self.kinesis.data, zlib.MAX_WBITS | 32))


class KinesisDataStreamModel(BaseModel):
    Records: List[KinesisDataStreamRecord]


def extract_cloudwatch_logs_from_event(event: KinesisDataStreamModel) -> List[CloudWatchLogsDecode]:
    return [CloudWatchLogsDecode(**record.decompress_zlib_record_data_as_json()) for record in event.Records]


def extract_cloudwatch_logs_from_record(record: KinesisDataStreamRecord) -> CloudWatchLogsDecode:
    return CloudWatchLogsDecode(**record.decompress_zlib_record_data_as_json())
