from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.utilities.streaming.s3_object import S3Object
from aws_lambda_powertools.utilities.streaming.transformations import (
    CsvTransform,
    GzipTransform,
)

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict[str, str], context: LambdaContext):
    s3 = S3Object(bucket=event["bucket"], key=event["key"])
    s3.transform([GzipTransform(), CsvTransform()], in_place=True)
    for line in s3:
        print(line)  # returns a dict
