from __future__ import annotations

from pydantic import BaseModel, PositiveInt, field_validator

from aws_lambda_powertools.shared.functions import base64_decode


class KinesisFirehoseRecordMetadata(BaseModel):
    shardId: str
    partitionKey: str
    approximateArrivalTimestamp: PositiveInt
    sequenceNumber: str
    subsequenceNumber: int


class KinesisFirehoseRecord(BaseModel):
    data: bytes | type[BaseModel]  # base64 encoded str is parsed into bytes
    recordId: str
    approximateArrivalTimestamp: PositiveInt
    kinesisRecordMetadata: KinesisFirehoseRecordMetadata | None = None

    @field_validator("data", mode="before")
    def data_base64_decode(cls, value):
        return base64_decode(value)


class KinesisFirehoseModel(BaseModel):
    invocationId: str
    deliveryStreamArn: str
    region: str
    sourceKinesisStreamArn: str | None = None
    records: list[KinesisFirehoseRecord]
