from __future__ import annotations

import json

from pydantic import BaseModel, PositiveInt, field_validator

from aws_lambda_powertools.shared.functions import base64_decode
from aws_lambda_powertools.utilities.parser.models import KinesisFirehoseRecordMetadata  # noqa: TCH001
from aws_lambda_powertools.utilities.parser.models.sqs import SqsRecordModel  # noqa: TCH001


class KinesisFirehoseSqsRecord(BaseModel):
    data: SqsRecordModel
    recordId: str
    approximateArrivalTimestamp: PositiveInt
    kinesisRecordMetadata: KinesisFirehoseRecordMetadata | None = None

    @field_validator("data", mode="before")
    def data_base64_decode(cls, value):
        # Firehose payload is encoded
        return json.loads(base64_decode(value))


class KinesisFirehoseSqsModel(BaseModel):
    invocationId: str
    deliveryStreamArn: str
    region: str
    sourceKinesisStreamArn: str | None = None
    records: list[KinesisFirehoseSqsRecord]
