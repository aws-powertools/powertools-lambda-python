from typing import Dict

from aws_lambda_powertools.utilities.streaming.s3_object import S3Object
from aws_lambda_powertools.utilities.streaming.transformations import CsvTransform
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: Dict[str, str], context: LambdaContext):
    s3 = S3Object(bucket=event["bucket"], key=event["key"])

    tsv_stream = s3.transform(CsvTransform(delimiter="\t"))
    for obj in tsv_stream:
        print(obj)
