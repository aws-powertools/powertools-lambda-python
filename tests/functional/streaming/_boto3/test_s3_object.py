from __future__ import annotations

import gzip
import io
from csv import DictReader
from gzip import GzipFile

import boto3
import pytest
from botocore import stub

from aws_lambda_powertools.utilities.streaming import S3Object
from aws_lambda_powertools.utilities.streaming._s3_seekable_io import _S3SeekableIO
from aws_lambda_powertools.utilities.streaming.compat import PowertoolsStreamingBody
from aws_lambda_powertools.utilities.streaming.transformations import GzipTransform


@pytest.fixture
def s3_client():
    return boto3.client("s3")


@pytest.fixture
def s3_client_stub(s3_client):
    with stub.Stubber(s3_client) as s3_stub:
        yield s3_stub


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


@pytest.mark.parametrize("is_gzip", [False, True], ids=["raw", "gzip"])
@pytest.mark.parametrize(
    "readline_kwargs, expected",
    [
        pytest.param({"size": 0}, b"", id="zero"),
        pytest.param({"size": 2}, b"he", id="short"),
        pytest.param({}, b"hello world\n", id="default"),
        pytest.param({"size": -1}, b"hello world\n", id="negative"),
        pytest.param({"size": None}, b"hello world\n", id="none"),
        pytest.param({"size": 100}, b"hello world\n", id="past-newline"),
    ],
)
def test_s3_readline_respects_size(s3_client, s3_client_stub, is_gzip, readline_kwargs, expected):
    payload = b"hello world\nnext line\n"
    wire_payload = gzip.compress(payload) if is_gzip else payload
    streaming_body = PowertoolsStreamingBody(raw_stream=io.BytesIO(wire_payload), content_length=len(wire_payload))
    s3_client_stub.add_response(
        "get_object",
        {"Body": streaming_body},
        {"Bucket": "bucket", "Key": "key", "Range": "bytes=0-"},
    )

    with S3Object(bucket="bucket", key="key", boto3_client=s3_client, is_gzip=is_gzip) as obj:
        assert obj.readline(**readline_kwargs) == expected
        assert obj.tell() == len(expected)
        assert obj.read() == payload[len(expected) :]
        assert obj.tell() == len(payload)
        assert obj.readline(**readline_kwargs) == b""
        assert obj.tell() == len(payload)

    s3_client_stub.assert_no_pending_responses()
