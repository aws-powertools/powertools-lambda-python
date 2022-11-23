import io
from typing import IO, Optional

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
