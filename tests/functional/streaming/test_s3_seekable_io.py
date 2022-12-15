import io

import boto3
import pytest
from botocore import stub

from aws_lambda_powertools.utilities.streaming._s3_seekable_io import _S3SeekableIO
from aws_lambda_powertools.utilities.streaming.compat import PowertoolsStreamingBody


@pytest.fixture
def s3_client():
    return boto3.client("s3")


@pytest.fixture
def s3_seekable_obj(s3_client):
    return _S3SeekableIO(bucket="bucket", key="key", boto3_client=s3_client)


@pytest.fixture
def s3_client_stub(s3_client):
    s3_stub = stub.Stubber(s3_client)
    s3_stub.activate()
    return s3_stub


def test_seekable(s3_seekable_obj):
    assert s3_seekable_obj.seekable() is True


def test_readable(s3_seekable_obj):
    assert s3_seekable_obj.readable() is True


def test_writeable(s3_seekable_obj):
    assert s3_seekable_obj.writable() is False


def test_tell_is_zero(s3_seekable_obj):
    assert s3_seekable_obj.tell() == 0


def test_seek_set_changes_position(s3_seekable_obj):
    assert s3_seekable_obj.seek(300, io.SEEK_SET) == 300
    assert s3_seekable_obj.tell() == 300


def test_seek_cur_changes_position(s3_seekable_obj):
    assert s3_seekable_obj.seek(200, io.SEEK_CUR) == 200
    assert s3_seekable_obj.seek(100, io.SEEK_CUR) == 300
    assert s3_seekable_obj.tell() == 300


def test_seek_end(s3_seekable_obj, s3_client_stub):
    s3_client_stub.add_response("head_object", {"ContentLength": 1000})

    assert s3_seekable_obj.seek(0, io.SEEK_END) == 1000
    assert s3_seekable_obj.tell() == 1000


def test_size(s3_seekable_obj, s3_client_stub):
    s3_client_stub.add_response("head_object", {"ContentLength": 1000})

    assert s3_seekable_obj.size == 1000


def test_raw_stream_fetches_with_range_header(s3_seekable_obj, s3_client_stub):
    s3_client_stub.add_response(
        "get_object",
        {"Body": ""},
        {"Bucket": s3_seekable_obj.bucket, "Key": s3_seekable_obj.key, "Range": "bytes=0-"},
    )

    assert s3_seekable_obj.raw_stream is not None


def test_raw_stream_fetches_with_range_header_after_seek(s3_seekable_obj, s3_client_stub):
    s3_seekable_obj.seek(100, io.SEEK_SET)

    s3_client_stub.add_response(
        "get_object",
        {"Body": ""},
        {"Bucket": s3_seekable_obj.bucket, "Key": s3_seekable_obj.key, "Range": "bytes=100-"},
    )

    assert s3_seekable_obj.raw_stream is not None


def test_read(s3_seekable_obj, s3_client_stub):
    payload = b"hello world"
    streaming_body = PowertoolsStreamingBody(raw_stream=io.BytesIO(payload), content_length=len(payload))

    s3_client_stub.add_response(
        "get_object",
        {"Body": streaming_body},
        {"Bucket": s3_seekable_obj.bucket, "Key": s3_seekable_obj.key, "Range": "bytes=0-"},
    )

    assert s3_seekable_obj.read(5) == b"hello"
    assert s3_seekable_obj.read(1) == b" "
    assert s3_seekable_obj.read(10) == b"world"
    assert s3_seekable_obj.tell() == len(payload)


def test_readline(s3_seekable_obj, s3_client_stub):
    payload = b"hello world\nworld hello"
    streaming_body = PowertoolsStreamingBody(raw_stream=io.BytesIO(payload), content_length=len(payload))

    s3_client_stub.add_response(
        "get_object",
        {"Body": streaming_body},
        {"Bucket": s3_seekable_obj.bucket, "Key": s3_seekable_obj.key, "Range": "bytes=0-"},
    )

    assert s3_seekable_obj.readline() == b"hello world\n"
    assert s3_seekable_obj.readline() == b"world hello"
    assert s3_seekable_obj.tell() == len(payload)


def test_readlines(s3_seekable_obj, s3_client_stub):
    payload = b"hello world\nworld hello"
    streaming_body = PowertoolsStreamingBody(raw_stream=io.BytesIO(payload), content_length=len(payload))

    s3_client_stub.add_response(
        "get_object",
        {"Body": streaming_body},
        {"Bucket": s3_seekable_obj.bucket, "Key": s3_seekable_obj.key, "Range": "bytes=0-"},
    )

    assert s3_seekable_obj.readlines() == [b"hello world\n", b"world hello"]
    assert s3_seekable_obj.tell() == len(payload)


def test_closed(s3_seekable_obj, s3_client_stub):
    payload = b"test"
    streaming_body = PowertoolsStreamingBody(raw_stream=io.BytesIO(payload), content_length=len(payload))

    s3_client_stub.add_response(
        "get_object",
        {"Body": streaming_body},
        {"Bucket": s3_seekable_obj.bucket, "Key": s3_seekable_obj.key, "Range": "bytes=0-"},
    )

    s3_seekable_obj.close()
    assert s3_seekable_obj.closed is True


def test_next(s3_seekable_obj, s3_client_stub):
    payload = b"test"
    streaming_body = PowertoolsStreamingBody(raw_stream=io.BytesIO(payload), content_length=len(payload))

    s3_client_stub.add_response(
        "get_object",
        {"Body": streaming_body},
        {"Bucket": s3_seekable_obj.bucket, "Key": s3_seekable_obj.key, "Range": "bytes=0-"},
    )

    assert next(s3_seekable_obj) == b"test"
    with pytest.raises(StopIteration):
        next(s3_seekable_obj)


def test_context_manager(s3_seekable_obj, s3_client_stub):
    payload = b"test"
    streaming_body = PowertoolsStreamingBody(raw_stream=io.BytesIO(payload), content_length=len(payload))

    s3_client_stub.add_response(
        "get_object",
        {"Body": streaming_body},
        {"Bucket": s3_seekable_obj.bucket, "Key": s3_seekable_obj.key, "Range": "bytes=0-"},
    )

    with s3_seekable_obj as f:
        assert f.read(4) == b"test"

    assert s3_seekable_obj.closed is True


def test_fileno(s3_seekable_obj):
    with pytest.raises(NotImplementedError):
        s3_seekable_obj.fileno()


def test_flush(s3_seekable_obj):
    with pytest.raises(NotImplementedError):
        s3_seekable_obj.flush()


def test_isatty(s3_seekable_obj):
    assert s3_seekable_obj.isatty() is False


def test_truncate(s3_seekable_obj):
    with pytest.raises(NotImplementedError):
        s3_seekable_obj.truncate()


def test_write(s3_seekable_obj):
    with pytest.raises(NotImplementedError):
        s3_seekable_obj.write(b"data")
