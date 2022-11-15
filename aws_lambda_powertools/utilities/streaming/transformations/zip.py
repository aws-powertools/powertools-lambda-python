import io
import typing
from zipfile import ZipFile

from aws_lambda_powertools.utilities.streaming.transformations.base import BaseTransform


class ZipTransform(BaseTransform):
    def transform(self, input_stream: io.RawIOBase) -> ZipFile:
        input_as_io = typing.cast(typing.IO[bytes], input_stream)
        return ZipFile(input_as_io, mode="r", **self.kwargs)
