import io
import json
from json import JSONDecodeError
from typing import Optional

from aws_lambda_powertools.utilities.streaming.transformations.base import BaseTransform


class JsonDeserializer(io.RawIOBase):
    def __init__(self, input_stream: io.RawIOBase):
        self.input = input_stream

    def read(self, size: int = -1) -> Optional[bytes]:
        return self.input.read(size)

    def readline(self, size: Optional[int] = None) -> bytes:
        return self.input.readline(size)

    def read_object(self) -> dict:
        obj: dict = {}

        while not self.input.closed:
            line = self.input.__next__()
            try:
                obj = json.loads(line)
            except JSONDecodeError:
                continue
            break

        return obj

    def __next__(self):
        return self.read_object()


class JsonTransform(BaseTransform):
    def transform(self, input_stream: io.RawIOBase) -> JsonDeserializer:
        return JsonDeserializer(input_stream=input_stream)
