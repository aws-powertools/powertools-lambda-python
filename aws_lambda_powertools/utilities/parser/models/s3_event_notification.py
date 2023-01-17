from pydantic import Json

from aws_lambda_powertools.utilities.parser.models.s3 import S3Model
from aws_lambda_powertools.utilities.parser.models.sqs import SqsRecordModel  
  
class SqsS3EventNotificationModel(SqsRecordModel):
  body: Json[S3Model]
