import csv
import io
from csv import DictReader
from typing import IO

from aws_lambda_powertools.utilities.streaming.transformations.base import BaseTransform


class CsvTransform(BaseTransform):
    def transform(self, input_stream: IO[bytes]) -> DictReader:
        encoding = self.kwargs.get("encoding", "utf-8")
        newline = self.kwargs.get("newline")

        # csv module needs an Iterator[str], so we wrap the underlying stream into a TextIO
        iterator = io.TextIOWrapper(input_stream, encoding=encoding, newline=newline)
        return csv.DictReader(iterator, *self.args, **self.kwargs)
