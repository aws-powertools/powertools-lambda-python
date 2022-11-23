from csv import DictReader

from aws_lambda_powertools.utilities.streaming import S3Object
from aws_lambda_powertools.utilities.streaming.transformations import (
    CsvTransform,
    GzipTransform,
)


def test_s3_pipeline_result():
    obj = S3Object(bucket="bucket", key="key")

    # Apply your transformations
    obj.transform([GzipTransform(), CsvTransform()], in_place=True)

    # Check the object at the end of the pipeline is a csv.DictReader (and not a gzip.GzipFile)
    assert type(obj.transformed_stream) is DictReader
