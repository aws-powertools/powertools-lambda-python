from typing import List, Optional, Type, Union

from pydantic import BaseModel, PositiveInt, field_validator

from aws_lambda_powertools.shared.functions import base64_decode


class KinesisFirehoseRecordMetadata(BaseModel):
    shardId: str
    partitionKey: str
    approximateArrivalTimestamp: PositiveInt
    sequenceNumber: str
    subsequenceNumber: int


class KinesisFirehoseRecord(BaseModel):
    data: Union[bytes, Type[BaseModel]]  # base64 encoded str is parsed into bytes
    recordId: str
    approximateArrivalTimestamp: PositiveInt
    kinesisRecordMetadata: Optional[KinesisFirehoseRecordMetadata] = None

    @field_validator("data", mode="before")
    def data_base64_decode(cls, value):
        return base64_decode(value)


class KinesisFirehoseModel(BaseModel):
    invocationId: str
    deliveryStreamArn: str
    region: str
    sourceKinesisStreamArn: Optional[str] = None
    records: List[KinesisFirehoseRecord]
