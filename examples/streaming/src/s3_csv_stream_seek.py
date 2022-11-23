import io
from typing import Dict

from aws_lambda_powertools.utilities.streaming.s3_object import S3Object
from aws_lambda_powertools.utilities.streaming.transformations import CsvTransform
from aws_lambda_powertools.utilities.typing import LambdaContext

"""
Assuming the CSV files contains rows after the header always has 8 bytes + 1 byte newline:

21.3,5,+
23.4,4,+
21.3,0,-
"""


def lambda_handler(event: Dict[str, str], context: LambdaContext):
    s3 = S3Object(bucket=event["bucket"], key=event["key"])

    # Jump 100 lines of 9 bytes each (8 bytes of data + 1 byte newline)
    s3.seek(100 * 9, io.SEEK_SET)

    s3.transform(CsvTransform(), in_place=True)
    for obj in s3:
        print(obj)
