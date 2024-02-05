import io

import boto3
from assert_transformation_module import UpperTransform
from botocore import stub

from aws_lambda_powertools.utilities.streaming import S3Object
from aws_lambda_powertools.utilities.streaming.compat import PowertoolsStreamingBody


def test_upper_transform():
    # GIVEN
    data_stream = io.BytesIO(b"hello world")
    # WHEN
    data_stream = UpperTransform().transform(data_stream)
    # THEN
    assert data_stream.read() == b"HELLO WORLD"


def test_s3_object_with_upper_transform():
    # GIVEN
    payload = b"hello world"
    s3_client = boto3.client("s3")
    s3_stub = stub.Stubber(s3_client)
    s3_stub.add_response(
        "get_object",
        {"Body": PowertoolsStreamingBody(raw_stream=io.BytesIO(payload), content_length=len(payload))},
    )
    s3_stub.activate()

    # WHEN
    data_stream = S3Object(bucket="bucket", key="key", boto3_client=s3_client)
    data_stream.transform(UpperTransform(), in_place=True)

    # THEN
    assert data_stream.read() == b"HELLO WORLD"
