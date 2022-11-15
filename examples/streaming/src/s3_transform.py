from typing import Dict

from aws_lambda_powertools.utilities.streaming.s3 import S3Object
from aws_lambda_powertools.utilities.streaming.transformations import (
    GzipTransform,
    JsonTransform,
)
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: Dict[str, str], context: LambdaContext):
    s3 = S3Object(bucket=event["bucket"], key=event["key"])
    data = s3.transform([GzipTransform(), JsonTransform()])
    for line in data:
        print(line)  # returns a dict
