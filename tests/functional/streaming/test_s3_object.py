import io
from csv import DictReader
from gzip import GzipFile

import boto3
import pytest
from botocore import stub
from botocore.response import StreamingBody

from aws_lambda_powertools.utilities.streaming import S3Object
from aws_lambda_powertools.utilities.streaming._s3_seekable_io import _S3SeekableIO
from aws_lambda_powertools.utilities.streaming.transformations import GzipTransform


def test_s3_basic_stream():
    obj = S3Object(bucket="bucket", key="key")
    assert type(obj.transformed_stream) is _S3SeekableIO


def test_s3_gzip_stream():
    obj = S3Object(bucket="bucket", key="key", gunzip=True)
    assert type(obj.transformed_stream) is GzipFile


def test_s3_csv_stream():
    obj = S3Object(bucket="bucket", key="key", csv=True)
    assert type(obj.transformed_stream) is DictReader


def test_s3_gzip_csv_stream():
    obj = S3Object(bucket="bucket", key="key", gunzip=True, csv=True)
    assert type(obj.transformed_stream) is DictReader


def test_s3_transform():
    obj = S3Object(bucket="bucket", key="key")

    new_obj = obj.transform(GzipTransform())
    assert type(new_obj) is GzipFile


def test_s3_transform_in_place():
    obj = S3Object(bucket="bucket", key="key")

    new_obj = obj.transform(GzipTransform(), in_place=True)
    assert new_obj is None


def test_s3_transform_after_read():
    # GIVEN a S3 Object with a "hello world" payload
    payload = b"hello world"

    s3_client = boto3.client("s3")
    s3_stub = stub.Stubber(s3_client)
    s3_stub.add_response(
        "get_object", {"Body": StreamingBody(raw_stream=io.BytesIO(payload), content_length=len(payload))}
    )
    s3_stub.activate()
    obj = S3Object(bucket="bucket", key="key", boto3_s3_client=s3_client)

    # WHEN you read some part of the object and then apply a transformation
    assert obj.read(5) == b"hello"

    # THEN it raises ValueError
    with pytest.raises(ValueError):
        obj.transform(GzipTransform())
