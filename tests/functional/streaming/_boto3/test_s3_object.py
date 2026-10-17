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
from aws_lambda_powertools.utilities.streaming.transformations import CsvTransform, GzipTransform, ZipTransform


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


@pytest.mark.parametrize("is_gzip", [False, True], ids=["raw", "gzip"])
def test_s3_closed_after_close_without_reading(s3_client, is_gzip):
    # GIVEN an object that was never read nor inspected
    obj = S3Object(bucket="bucket", key="key", boto3_client=s3_client, is_gzip=is_gzip)

    # WHEN it is closed
    obj.close()

    # THEN it reports as closed, whether or not data transformations are configured
    assert obj.closed is True


def test_s3_closed_does_not_make_requests_for_zip(s3_client, s3_client_stub):
    # GIVEN an object with a zip transformation, which would read the archive as soon as it is created
    obj = S3Object(bucket="bucket", key="key", boto3_client=s3_client)
    obj.transform(ZipTransform(), in_place=True)

    # WHEN checking whether it is closed
    # THEN no S3 request is issued (the stubber has no responses queued, so any call would fail)
    assert obj.closed is False
    s3_client_stub.assert_no_pending_responses()


def _stub_get_object(s3_client_stub, payload: bytes):
    streaming_body = PowertoolsStreamingBody(raw_stream=io.BytesIO(payload), content_length=len(payload))
    s3_client_stub.add_response("get_object", {"Body": streaming_body})


def test_csv_transform_keeps_options_when_reused(s3_client, s3_client_stub):
    # GIVEN a single CsvTransform with a non-default encoding applied to two objects
    transform = CsvTransform(encoding="latin-1", delimiter=";")
    payload = "name;city\ncafé;Zürich\n".encode("latin-1")

    for _ in range(2):
        _stub_get_object(s3_client_stub, payload)

        # WHEN each object is transformed
        rows = list(S3Object(bucket="bucket", key="key", boto3_client=s3_client).transform(transform))

        # THEN the encoding is honoured every time, not only on the first use
        assert rows == [{"name": "café", "city": "Zürich"}]

    assert transform.transform_options == {"encoding": "latin-1", "delimiter": ";"}
