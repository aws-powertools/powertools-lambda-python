from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING

from aws_lambda_powertools.utilities.streaming.s3_object import S3Object
from aws_lambda_powertools.utilities.streaming.transformations import ZipTransform

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict[str, str], context: LambdaContext):
    s3 = S3Object(bucket=event["bucket"], key=event["key"])

    zf = s3.transform(ZipTransform(compression=zipfile.ZIP_LZMA))

    print(zf.nameslist())
    zf.extract(zf.namelist()[0], "/tmp")
