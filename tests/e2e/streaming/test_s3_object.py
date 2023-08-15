import json

import boto3
import pytest

from tests.e2e.utils import data_fetcher


@pytest.fixture
def regular_bucket_name(infrastructure: dict) -> str:
    return infrastructure.get("RegularBucket", "")


@pytest.fixture
def versioned_bucket_name(infrastructure: dict) -> str:
    return infrastructure.get("VersionedBucket", "")


@pytest.fixture
def s3_object_handler_fn_arn(infrastructure: dict) -> str:
    return infrastructure.get("S3ObjectHandler", "")


@pytest.mark.xdist_group(name="streaming")
def get_object_version(bucket, key) -> str:
    s3 = boto3.client("s3")
    versions = s3.list_object_versions(Bucket=bucket)

    for version in versions["Versions"]:
        version_id = version["VersionId"]
        version_key = version["Key"]

        if version_key == key:
            return version_id

    raise ValueError(f"Cannot find versioned {key} inside {bucket}")


def get_lambda_result_payload(s3_object_handler_fn_arn: str, payload: dict) -> dict:
    handler_result, _ = data_fetcher.get_lambda_response(
        lambda_arn=s3_object_handler_fn_arn,
        payload=json.dumps(payload),
    )

    return json.loads(handler_result["Payload"].read())


@pytest.mark.xdist_group(name="streaming")
def test_s3_object_size(s3_object_handler_fn_arn, regular_bucket_name):
    payload = {"bucket": regular_bucket_name, "key": "plain.txt"}
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("size") == 12
    assert result.get("body") == "hello world"


@pytest.mark.xdist_group(name="streaming")
def test_s3_versioned_object_size(s3_object_handler_fn_arn, versioned_bucket_name):
    key = "plain.txt"
    payload = {
        "bucket": versioned_bucket_name,
        "key": key,
        "version_id": get_object_version(versioned_bucket_name, key),
    }
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("size") == 12
    assert result.get("body") == "hello world"


@pytest.mark.xdist_group(name="streaming")
def test_s3_object_non_existent(s3_object_handler_fn_arn, regular_bucket_name):
    payload = {"bucket": regular_bucket_name, "key": "NOTEXISTENT.txt"}
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("error") == "Not found"


@pytest.mark.xdist_group(name="streaming")
def test_s3_object_csv_constructor(s3_object_handler_fn_arn, regular_bucket_name):
    payload = {"bucket": regular_bucket_name, "key": "csv.txt", "is_csv": True}
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("body") == {"name": "hello", "value": "world"}


@pytest.mark.xdist_group(name="streaming")
def test_s3_versioned_object_csv_constructor(s3_object_handler_fn_arn, versioned_bucket_name):
    key = "csv.txt"
    payload = {
        "bucket": versioned_bucket_name,
        "key": key,
        "version_id": get_object_version(versioned_bucket_name, key),
        "is_csv": True,
    }
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("body") == {"name": "hello", "value": "world"}


@pytest.mark.xdist_group(name="streaming")
def test_s3_object_csv_transform(s3_object_handler_fn_arn, regular_bucket_name):
    payload = {"bucket": regular_bucket_name, "key": "csv.txt", "transform_csv": True}
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("body") == {"name": "hello", "value": "world"}


@pytest.mark.xdist_group(name="streaming")
def test_s3_object_csv_transform_in_place(s3_object_handler_fn_arn, regular_bucket_name):
    payload = {"bucket": regular_bucket_name, "key": "csv.txt", "transform_csv": True, "in_place": True}
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("body") == {"name": "hello", "value": "world"}


@pytest.mark.xdist_group(name="streaming")
def test_s3_object_csv_gzip_constructor(s3_object_handler_fn_arn, regular_bucket_name):
    payload = {"bucket": regular_bucket_name, "key": "csv.txt.gz", "is_csv": True, "is_gzip": True}
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("body") == {"name": "hello", "value": "world"}


@pytest.mark.xdist_group(name="streaming")
def test_s3_versioned_object_csv_gzip_constructor(s3_object_handler_fn_arn, versioned_bucket_name):
    key = "csv.txt.gz"
    payload = {
        "bucket": versioned_bucket_name,
        "key": key,
        "version_id": get_object_version(versioned_bucket_name, key),
        "is_csv": True,
        "is_gzip": True,
    }
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("body") == {"name": "hello", "value": "world"}


@pytest.mark.xdist_group(name="streaming")
def test_s3_object_gzip_constructor(s3_object_handler_fn_arn, regular_bucket_name):
    payload = {"bucket": regular_bucket_name, "key": "plain.txt.gz", "is_gzip": True}
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("body") == "hello world"


@pytest.mark.xdist_group(name="streaming")
def test_s3_versioned_object_gzip_constructor(s3_object_handler_fn_arn, versioned_bucket_name):
    key = "plain.txt.gz"
    payload = {
        "bucket": versioned_bucket_name,
        "key": key,
        "version_id": get_object_version(versioned_bucket_name, key),
        "is_gzip": True,
    }
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("body") == "hello world"


@pytest.mark.xdist_group(name="streaming")
def test_s3_object_gzip_transform(s3_object_handler_fn_arn, regular_bucket_name):
    payload = {"bucket": regular_bucket_name, "key": "plain.txt.gz", "transform_gzip": True}
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("body") == "hello world"


@pytest.mark.xdist_group(name="streaming")
def test_s3_object_gzip_transform_in_place(s3_object_handler_fn_arn, regular_bucket_name):
    payload = {"bucket": regular_bucket_name, "key": "plain.txt.gz", "transform_gzip": True, "in_place": True}
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("body") == "hello world"


@pytest.mark.xdist_group(name="streaming")
def test_s3_object_zip_transform(s3_object_handler_fn_arn, regular_bucket_name):
    payload = {"bucket": regular_bucket_name, "key": "fileset.zip", "transform_zip": True}
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("manifest") == ["1.txt", "2.txt"]
    assert result.get("body") == "This is file 2"


@pytest.mark.xdist_group(name="streaming")
def test_s3_object_zip_transform_in_place(s3_object_handler_fn_arn, regular_bucket_name):
    payload = {"bucket": regular_bucket_name, "key": "fileset.zip", "transform_zip": True, "in_place": True}
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("manifest") == ["1.txt", "2.txt"]
    assert result.get("body") == "This is file 2"


@pytest.mark.xdist_group(name="streaming")
def test_s3_object_zip_lzma_transform(s3_object_handler_fn_arn, regular_bucket_name):
    payload = {"bucket": regular_bucket_name, "key": "fileset.zip.lzma", "transform_zip_lzma": True}
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("manifest") == ["1.txt", "2.txt"]
    assert result.get("body") == "This is file 2"


@pytest.mark.xdist_group(name="streaming")
def test_s3_object_zip_lzma_transform_in_place(s3_object_handler_fn_arn, regular_bucket_name):
    payload = {"bucket": regular_bucket_name, "key": "fileset.zip.lzma", "transform_zip_lzma": True, "in_place": True}
    result = get_lambda_result_payload(s3_object_handler_fn_arn, payload)
    assert result.get("manifest") == ["1.txt", "2.txt"]
    assert result.get("body") == "This is file 2"
