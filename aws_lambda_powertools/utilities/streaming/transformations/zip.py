from typing import IO
from zipfile import ZipFile

from aws_lambda_powertools.utilities.streaming.transformations.base import BaseTransform


class ZipTransform(BaseTransform):
    def transform(self, input_stream: IO[bytes]) -> ZipFile:
        return ZipFile(input_stream, mode="r", **self.kwargs)
