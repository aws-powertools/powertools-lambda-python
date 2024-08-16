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

    BatchTypeModels = Optional[
        Union[Type[SqsRecordModel], Type[DynamoDBStreamRecordModel], Type[KinesisDataStreamRecordModel]]
    ]
    BatchSqsTypeModel = Optional[Type[SqsRecordModel]]
else:  # pragma: no cover
    BatchTypeModels = "BatchTypeModels"  # type: ignore
    BatchSqsTypeModel = "BatchSqsTypeModel"  # type: ignore


class PartialItemFailures(TypedDict):
    itemIdentifier: str


class PartialItemFailureResponse(TypedDict):
    batchItemFailures: list[PartialItemFailures]
