import csv
import io
from csv import DictReader
from typing import IO

from aws_lambda_powertools.utilities.streaming.transformations.base import BaseTransform


class CsvTransform(BaseTransform):
    """
    CSV data transform.

    Returns a csv.DictReader that reads data from the input stream:
    https://docs.python.org/3/library/csv.html#csv.DictReader

    Example
    -------

        >>> from aws_lambda_powertools.utilities.streaming import S3Object
        >>> from aws_lambda_powertools.utilities.streaming.transformations import CsvTransform
        >>>
        >>> s3object = S3Object(bucket="bucket", key="key")
        >>> csv_reader = s3object.transform(CsvTransform())
        >>> for row in csv_reader:
        >>>   print(row)

    Since the underlying stream of bytes needs to be converted into a stream of characters (Iterator[str]),
    we wrap the input into an io.TextIOWrapper. This means you have control over the text encoding
    and line termination options.

        >>> from aws_lambda_powertools.utilities.streaming import S3Object
        >>> from aws_lambda_powertools.utilities.streaming.transformations import CsvTransform
        >>>
        >>> s3object = S3Object(bucket="bucket", key="key")
        >>> csv_reader = s3object.transform(CsvTransform(encoding="utf-8", newline="\\r\\n"))
        >>> for row in csv_reader:
        >>>   print(row)

    Additional options passed on the constructor, will be pased to the csv.DictReader constructor.

        >>> from aws_lambda_powertools.utilities.streaming import S3Object
        >>> from aws_lambda_powertools.utilities.streaming.transformations import CsvTransform
        >>>
        >>> s3object = S3Object(bucket="bucket", key="key")
        >>> csv_reader = s3object.transform(CsvTransform(dialect="excel"))
        >>> for row in csv_reader:
        >>>   print(row)
    """

    def transform(self, input_stream: IO[bytes]) -> DictReader:
        encoding = self.transform_options.pop("encoding", "utf-8")
        newline = self.transform_options.pop("newline", None)

        # csv module needs an Iterator[str], so we wrap the underlying stream into a TextIO
        iterator = io.TextIOWrapper(input_stream, encoding=encoding, newline=newline)
        return csv.DictReader(iterator, **self.transform_options)
