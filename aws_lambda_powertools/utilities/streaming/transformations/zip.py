from typing import IO
from zipfile import ZipFile

from aws_lambda_powertools.utilities.streaming.transformations.base import BaseTransform


class ZipTransform(BaseTransform):
    """
    Zip data transform.

    Returns a zip.ZipFile that reads data from the input stream:
    https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile

    Currently, it's not possible to pipe the zip file stream into another data transformation,
    since a Zip file contains multiple files, and not a single stream.

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

    Additional options passed on the constructor, will be pased to the csv.DictReader constructor.

        >>> from aws_lambda_powertools.utilities.streaming import S3Object
        >>> from aws_lambda_powertools.utilities.streaming.transformations import ZipTransform
        >>> import zipfile
        >>>
        >>> s3object = S3Object(bucket="bucket", key="key")
        >>> zip_reader = s3object.transform(ZipTransform(compression=zipfile.ZIP_LZMA))
        >>> for file in zip_reader.namelist():
        >>>   print(file)
        >>>   zip_reader.extract(file)

    """

    def transform(self, input_stream: IO[bytes]) -> ZipFile:
        return ZipFile(input_stream, mode="r", **self.kwargs)
