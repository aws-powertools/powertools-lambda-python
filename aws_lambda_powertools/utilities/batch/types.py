from __future__ import annotations

import sys
from typing import Optional, Type, TypedDict, Union

has_pydantic = "pydantic" in sys.modules

# For IntelliSense and Mypy to work, we need to account for possible SQS subclasses
# We need them as subclasses as we must access their message ID or sequence number metadata via dot notation
if has_pydantic:  # pragma: no cover
    from aws_lambda_powertools.utilities.parser.models import DynamoDBStreamRecordModel, SqsRecordModel
    from aws_lambda_powertools.utilities.parser.models import (
        KinesisDataStreamRecord as KinesisDataStreamRecordModel,
    )
    from aws_lambda_powertools.utilities.parser.models.kafka import KafkaRecordModel

    BatchTypeModels = Optional[
        Union[
            Type[SqsRecordModel],
            Type[DynamoDBStreamRecordModel],
            Type[KinesisDataStreamRecordModel],
            Type[KafkaRecordModel],
        ]
    ]
    BatchSqsTypeModel = Optional[Type[SqsRecordModel]]
else:  # pragma: no cover
    BatchTypeModels = "BatchTypeModels"  # type: ignore
    BatchSqsTypeModel = "BatchSqsTypeModel"  # type: ignore


class KafkaItemIdentifier(TypedDict):
    """Kafka uses a composite identifier with partition and offset."""

    partition: str
    offset: int


class PartialItemFailures(TypedDict):
    """
    Represents a partial item failure response.

    For SQS, Kinesis, and DynamoDB: itemIdentifier is a string (message_id or sequence_number)
    For Kafka: itemIdentifier is a KafkaItemIdentifier dict with partition and offset
    """

    itemIdentifier: str | KafkaItemIdentifier


class PartialItemFailureResponse(TypedDict):
    batchItemFailures: list[PartialItemFailures]
