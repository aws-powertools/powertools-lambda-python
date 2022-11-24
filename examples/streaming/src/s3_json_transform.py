import io
from typing import IO, Optional

import ijson

from aws_lambda_powertools.utilities.streaming.transformations import BaseTransform


# Using io.RawIOBase gets us default implementations of many of the common IO methods
class JsonDeserializer(io.RawIOBase):
    def __init__(self, input_stream: IO[bytes]):
        self.input = ijson.items(input_stream, "", multiple_values=True)

    def read(self, size: int = -1) -> Optional[bytes]:
        raise NotImplementedError(f"{__name__} does not implement read")

    def readline(self, size: Optional[int] = None) -> bytes:
        raise NotImplementedError(f"{__name__} does not implement readline")

    def read_object(self) -> dict:
        return self.input.__next__()

    def __next__(self):
        return self.read_object()


class JsonTransform(BaseTransform):
    def transform(self, input_stream: IO[bytes]) -> JsonDeserializer:
        return JsonDeserializer(input_stream=input_stream)
