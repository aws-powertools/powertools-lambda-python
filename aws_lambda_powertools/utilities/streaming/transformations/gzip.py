from gzip import GzipFile
from typing import IO

from aws_lambda_powertools.utilities.streaming.transformations.base import BaseTransform


class GzipTransform(BaseTransform):
    """
    Gzip data transform.

    Returns a gzip.GzipFile instead that reads data from the input stream:
    https://docs.python.org/3/library/gzip.html#gzip.GzipFile

    Example
    -------

        >>> from aws_lambda_powertools.utilities.streaming import S3Object
        >>> from aws_lambda_powertools.utilities.streaming.transformations import GzipTransform
        >>>
        >>> s3object = S3Object(bucket="bucket", key="key")
        >>> reader = s3object.transform(GzipTransform())
        >>> for line in reader:
        >>>   print(line)

    """

    def transform(self, input_stream: IO[bytes]) -> GzipFile:
        return GzipFile(fileobj=input_stream, mode="rb", **self.transform_options)
