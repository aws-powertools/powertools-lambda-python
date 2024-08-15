from __future__ import annotations

from pydantic import Json  # noqa: TCH002

from aws_lambda_powertools.utilities.parser.models.s3 import S3Model  # noqa: TCH001
from aws_lambda_powertools.utilities.parser.models.sqs import SqsModel, SqsRecordModel


class S3SqsEventNotificationRecordModel(SqsRecordModel):
    body: Json[S3Model]


class S3SqsEventNotificationModel(SqsModel):
    Records: list[S3SqsEventNotificationRecordModel]
