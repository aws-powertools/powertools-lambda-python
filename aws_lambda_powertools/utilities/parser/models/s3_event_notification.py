from typing import List

from pydantic import Json

from aws_lambda_powertools.utilities.parser.models.s3 import S3Model
from aws_lambda_powertools.utilities.parser.models.sqs import SqsModel, SqsRecordModel


class S3SqsEventNotificationRecordModel(SqsRecordModel):  # type: ignore[override]
    body: Json[S3Model]


class S3SqsEventNotificationModel(SqsModel):  # type: ignore[override]
    Records: List[S3SqsEventNotificationRecordModel]
