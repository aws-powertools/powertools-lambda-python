from typing import Dict

from aws_lambda_powertools.utilities.streaming.s3_object import S3Object
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: Dict[str, str], context: LambdaContext):
    s3 = S3Object(bucket=event["bucket"], key=event["key"], version_id=event["version_id"])
    for line in s3:
        print(line)
