import io
from typing import Dict

from aws_lambda_powertools.utilities.streaming.s3_object import S3Object
from aws_lambda_powertools.utilities.streaming.transformations import CsvTransform
from aws_lambda_powertools.utilities.typing import LambdaContext

"""
Assuming the CSV files contains rows after the header always has 8 bytes + 1 byte newline:

reading,position,type
21.3,5,+
23.4,4,+
21.3,0,-
...
"""

CSV_HEADERS = ["reading", "position", "type"]
ROW_SIZE = 8 + 1  # 1 byte newline
HEADER_SIZE = 21 + 1  # 1 byte newline
LINES_TO_JUMP = 100


def lambda_handler(event: Dict[str, str], context: LambdaContext):
    sample_csv = S3Object(bucket=event["bucket"], key=event["key"])

    # Skip the header line
    sample_csv.seek(HEADER_SIZE, io.SEEK_SET)

    # Jump 100 lines of 9 bytes each (8 bytes of data + 1 byte newline)
    sample_csv.seek(LINES_TO_JUMP * ROW_SIZE, io.SEEK_CUR)

    sample_csv.transform(CsvTransform(), in_place=True)
    for row in sample_csv:
        print(row["reading"])
