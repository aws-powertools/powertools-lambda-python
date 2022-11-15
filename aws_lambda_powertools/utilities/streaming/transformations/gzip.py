import io
from gzip import GzipFile

from aws_lambda_powertools.utilities.streaming.transformations.base import BaseTransform


class GzipTransform(BaseTransform):
    def transform(self, input_stream: io.RawIOBase) -> GzipFile:
        return GzipFile(fileobj=input_stream, mode="rb", **self.kwargs)
