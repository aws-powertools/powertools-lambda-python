from csv import DictReader
from gzip import GzipFile

from aws_lambda_powertools.utilities.streaming import S3Object
from aws_lambda_powertools.utilities.streaming._s3_seekable_io import _S3SeekableIO
from aws_lambda_powertools.utilities.streaming.transformations import GzipTransform


def test_s3_basic_stream():
    obj = S3Object(bucket="bucket", key="key")
    assert type(obj.transformed_stream) is _S3SeekableIO


def test_s3_gzip_stream():
    obj = S3Object(bucket="bucket", key="key", is_gzip=True)
    assert type(obj.transformed_stream) is GzipFile


def test_s3_csv_stream():
    obj = S3Object(bucket="bucket", key="key", is_csv=True)
    assert type(obj.transformed_stream) is DictReader


def test_s3_gzip_csv_stream():
    obj = S3Object(bucket="bucket", key="key", is_gzip=True, is_csv=True)
    assert type(obj.transformed_stream) is DictReader


def test_s3_transform():
    obj = S3Object(bucket="bucket", key="key")

    new_obj = obj.transform(GzipTransform())
    assert type(new_obj) is GzipFile


def test_s3_transform_in_place():
    obj = S3Object(bucket="bucket", key="key")

    new_obj = obj.transform(GzipTransform(), in_place=True)
    assert new_obj is None
