from typing import IO
from zipfile import ZipFile

from aws_lambda_powertools.utilities.streaming.transformations.base import BaseTransform


class ZipTransform(BaseTransform):
    """
    Zip data transform.

    Returns a zip.ZipFile that reads data from the input stream:
    https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile

    Example
    -------

        >>> from aws_lambda_powertools.utilities.streaming import S3Object
        >>> from aws_lambda_powertools.utilities.streaming.transformations import ZipTransform
        >>>
        >>> s3object = S3Object(bucket="bucket", key="key")
        >>> zip_reader = s3object.transform(ZipTransform())
        >>> for file in zip_reader.namelist():
        >>>   print(file)
        >>>   zip_reader.extract(file)

    Additional options passed on the constructor, will be pased to the is_csv.DictReader constructor.

        >>> from aws_lambda_powertools.utilities.streaming import S3Object
        >>> from aws_lambda_powertools.utilities.streaming.transformations import ZipTransform
        >>> import zipfile
        >>>
        >>> s3object = S3Object(bucket="bucket", key="key")
        >>> zip_reader = s3object.transform(ZipTransform(compression=zipfile.ZIP_LZMA))
        >>> for file in zip_reader.namelist():
        >>>   print(file)
        >>>   zip_reader.extract(file)

    Currently, it's not possible to pipe the Zip file stream into another data transformation,
    since a Zip file contains multiple files, and not a single stream. However, you can still
    open a specific file as a stream, reading only the necessary bytes to extract it:

        >>> from aws_lambda_powertools.utilities.streaming import S3Object
        >>> from aws_lambda_powertools.utilities.streaming.transformations import ZipTransform
        >>> import zipfile
        >>>
        >>> s3object = S3Object(bucket="bucket", key="key")
        >>> zip_reader = s3object.transform(ZipTransform())
        >>> with zip_reader.open("filename.txt") as f:
        >>>   for line in f:
        >>>      print(line)
    """

    def transform(self, input_stream: IO[bytes]) -> ZipFile:
        return ZipFile(input_stream, mode="r", **self.transform_options)
