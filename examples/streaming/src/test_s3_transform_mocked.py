import io
from typing import IO, Optional

import boto3
from botocore import stub

from aws_lambda_powertools.utilities.streaming import S3Object
from aws_lambda_powertools.utilities.streaming.compat import PowertoolsStreamingBody
from aws_lambda_powertools.utilities.streaming.transformations import BaseTransform


class UpperIO(io.RawIOBase):
    def __init__(self, input_stream: IO[bytes], encoding: str):
        self.encoding = encoding
        self.input_stream = io.TextIOWrapper(input_stream, encoding=encoding)

    def read(self, size: int = -1) -> Optional[bytes]:
        data = self.input_stream.read(size)
        return data.upper().encode(self.encoding)


class UpperTransform(BaseTransform):
    def transform(self, input_stream: IO[bytes]) -> UpperIO:
        return UpperIO(input_stream=input_stream, encoding="utf-8")


def test_s3_pipeline_result():
    payload = b"hello world"

    s3_client = boto3.client("s3")
    s3_stub = stub.Stubber(s3_client)
    s3_stub.add_response(
        "get_object", {"Body": PowertoolsStreamingBody(raw_stream=io.BytesIO(payload), content_length=len(payload))}
    )
    s3_stub.activate()

    obj = S3Object(bucket="bucket", key="key", boto3_client=s3_client)
    uobj = obj.transform(UpperTransform())
    assert uobj.read() == b"HELLO WORLD"
