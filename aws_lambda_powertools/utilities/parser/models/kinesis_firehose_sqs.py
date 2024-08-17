import json
from typing import List, Optional

from pydantic import BaseModel, PositiveInt, field_validator

from aws_lambda_powertools.shared.functions import base64_decode
from aws_lambda_powertools.utilities.parser.models import KinesisFirehoseRecordMetadata

from .sqs import SqsRecordModel


class KinesisFirehoseSqsRecord(BaseModel):
    data: SqsRecordModel
    recordId: str
    approximateArrivalTimestamp: PositiveInt
    kinesisRecordMetadata: Optional[KinesisFirehoseRecordMetadata] = None

    @field_validator("data", mode="before")
    def data_base64_decode(cls, value):
        # Firehose payload is encoded
        return json.loads(base64_decode(value))


class KinesisFirehoseSqsModel(BaseModel):
    invocationId: str
    deliveryStreamArn: str
    region: str
    sourceKinesisStreamArn: Optional[str] = None
    records: List[KinesisFirehoseSqsRecord]
