import zipfile

import botocore.exceptions

from aws_lambda_powertools.utilities.streaming import S3Object
from aws_lambda_powertools.utilities.streaming.transformations import (
    CsvTransform,
    GzipTransform,
    ZipTransform,
)

"""
Event schema

bucket: str
key: str
version_id: str, optional

is_gzip: bool, optional
is_csv: bool, optional

transform_gunzip: bool, optional
transform_csv: bool, optional
transform_zip: bool, optional
transform_zip_lzma: bool, optional

transform_in_place: bool, optional
"""


def lambda_handler(event, context):
    bucket = event.get("bucket")
    key = event.get("key")
    version_id = event.get("version_id", None)

    gunzip = event.get("is_gzip", False)
    csv = event.get("is_csv", False)

    transform_gzip = event.get("transform_gzip", False)
    transform_csv = event.get("transform_csv", False)
    transform_zip = event.get("transform_zip", False)
    transform_zip_lzma = event.get("transform_zip_lzma", False)
    transform_in_place = event.get("transform_in_place", False)

    response = {}

    try:
        obj = S3Object(bucket=bucket, key=key, version_id=version_id, is_gzip=gunzip, is_csv=csv)
        response["size"] = obj.size

        transformations = []
        if transform_gzip:
            transformations.append(GzipTransform())
        if transform_zip:
            transformations.append(ZipTransform())
        if transform_csv:
            transformations.append(CsvTransform())
        if transform_zip_lzma:
            transformations.append(ZipTransform(compression=zipfile.ZIP_LZMA))

        if len(transformations) > 0:
            if transform_in_place:
                obj.transform(transformations, in_place=True)
            else:
                obj = obj.transform(transformations)

        if transform_zip or transform_zip_lzma:
            response["manifest"] = obj.namelist()
            response["body"] = (
                obj.read(obj.namelist()[1]).rstrip().decode("utf-8")
            )  # extracts the second file on the zip
        elif transform_csv or csv:
            response["body"] = obj.__next__()
        elif transform_gzip or gunzip:
            response["body"] = obj.readline().rstrip().decode("utf-8")
        else:
            response["body"] = obj.readline().rstrip().decode("utf-8")
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            response["error"] = "Not found"
        else:
            raise

    return response
