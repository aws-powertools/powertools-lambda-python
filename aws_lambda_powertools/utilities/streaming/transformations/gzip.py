from gzip import GzipFile
from typing import IO

from aws_lambda_powertools.utilities.streaming.transformations.base import BaseTransform


class GzipTransform(BaseTransform):
    def transform(self, input_stream: IO[bytes]) -> GzipFile:
        return GzipFile(fileobj=input_stream, mode="rb", **self.kwargs)
