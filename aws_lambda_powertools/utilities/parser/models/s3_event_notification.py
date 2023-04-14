from typing import List

from pydantic import Json

from aws_lambda_powertools.utilities.parser.models.s3 import S3Model
from aws_lambda_powertools.utilities.parser.models.sqs import SqsRecordModel, SqsModel
  
class SqsS3EventNotificationRecordModel(SqsRecordModel):
  body: Json[S3Model]

class SqsS3EventNotificationModel(SqsModel):
  Records: List[SqsS3EventNotificationRecordModel]
