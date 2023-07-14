import pytest

from aws_lambda_powertools.utilities.parser import ValidationError
from aws_lambda_powertools.utilities.parser.models import S3Model, S3RecordModel
from tests.functional.utils import load_event


def test_s3_trigger_event():
    raw_event = load_event("s3Event.json")
    parsed_event: S3Model = S3Model(**raw_event)

    records = list(parsed_event.Records)
    assert len(records) == 1

    record: S3RecordModel = records[0]
    raw_record = raw_event["Records"][0]
    assert record.eventVersion == raw_record["eventVersion"]
    assert record.eventSource == raw_record["eventSource"]
    assert record.awsRegion == raw_record["awsRegion"]
    convert_time = int(round(record.eventTime.timestamp() * 1000))
    assert convert_time == 1567539447192
    assert record.eventName == raw_record["eventName"]
    assert record.glacierEventData is None

    user_identity = record.userIdentity
    assert user_identity.principalId == raw_record["userIdentity"]["principalId"]

    request_parameters = record.requestParameters
    assert str(request_parameters.sourceIPAddress) == "205.255.255.255/32"
    assert record.responseElements.x_amz_request_id == raw_record["responseElements"]["x-amz-request-id"]
    assert record.responseElements.x_amz_id_2 == raw_record["responseElements"]["x-amz-id-2"]

    s3 = record.s3
    raw_s3 = raw_event["Records"][0]["s3"]
    assert s3.s3SchemaVersion == raw_record["s3"]["s3SchemaVersion"]
    assert s3.configurationId == raw_record["s3"]["configurationId"]
    assert s3.object.key == raw_s3["object"]["key"]
    assert s3.object.size == raw_s3["object"]["size"]
    assert s3.object.eTag == raw_s3["object"]["eTag"]
    assert s3.object.versionId is None
    assert s3.object.sequencer == raw_s3["object"]["sequencer"]

    bucket = s3.bucket
    raw_bucket = raw_record["s3"]["bucket"]
    assert bucket.name == raw_bucket["name"]
    assert bucket.ownerIdentity.principalId == raw_bucket["ownerIdentity"]["principalId"]
    assert bucket.arn == raw_bucket["arn"]


def test_s3_glacier_trigger_event():
    raw_event = load_event("s3EventGlacier.json")
    parsed_event: S3Model = S3Model(**raw_event)

    records = list(parsed_event.Records)
    assert len(records) == 1

    record: S3RecordModel = records[0]
    raw_record = raw_event["Records"][0]
    assert record.eventVersion == raw_record["eventVersion"]
    assert record.eventSource == raw_record["eventSource"]
    assert record.awsRegion == raw_record["awsRegion"]
    convert_time = int(round(record.eventTime.timestamp() * 1000))
    assert convert_time == 1567539447192
    assert record.eventName == raw_record["eventName"]
    assert record.glacierEventData is not None
    convert_time = int(
        round(record.glacierEventData.restoreEventData.lifecycleRestorationExpiryTime.timestamp() * 1000),
    )
    assert convert_time == 60000
    assert (
        record.glacierEventData.restoreEventData.lifecycleRestoreStorageClass
        == raw_record["glacierEventData"]["restoreEventData"]["lifecycleRestoreStorageClass"]
    )

    user_identity = record.userIdentity
    assert user_identity.principalId == raw_record["userIdentity"]["principalId"]

    request_parameters = record.requestParameters
    assert str(request_parameters.sourceIPAddress) == "205.255.255.255/32"
    assert record.responseElements.x_amz_request_id == raw_record["responseElements"]["x-amz-request-id"]
    assert record.responseElements.x_amz_id_2 == raw_record["responseElements"]["x-amz-id-2"]

    s3 = record.s3
    raw_s3 = raw_event["Records"][0]["s3"]
    assert s3.s3SchemaVersion == raw_record["s3"]["s3SchemaVersion"]
    assert s3.configurationId == raw_record["s3"]["configurationId"]
    assert s3.object.key == raw_s3["object"]["key"]
    assert s3.object.size == raw_s3["object"]["size"]
    assert s3.object.eTag == raw_s3["object"]["eTag"]
    assert s3.object.versionId is None
    assert s3.object.sequencer == raw_s3["object"]["sequencer"]

    bucket = s3.bucket
    raw_bucket = raw_record["s3"]["bucket"]
    assert bucket.name == raw_bucket["name"]
    assert bucket.ownerIdentity.principalId == raw_bucket["ownerIdentity"]["principalId"]
    assert bucket.arn == raw_bucket["arn"]


def test_s3_trigger_event_delete_object():
    raw_event = load_event("s3EventDeleteObject.json")
    parsed_event: S3Model = S3Model(**raw_event)

    records = list(parsed_event.Records)
    assert len(records) == 1

    record: S3RecordModel = records[0]
    raw_record = raw_event["Records"][0]
    assert record.eventVersion == raw_record["eventVersion"]
    assert record.eventSource == raw_record["eventSource"]
    assert record.awsRegion == raw_record["awsRegion"]
    convert_time = int(round(record.eventTime.timestamp() * 1000))
    assert convert_time == 1567539447192
    assert record.eventName == raw_record["eventName"]
    assert record.glacierEventData is None

    user_identity = record.userIdentity
    assert user_identity.principalId == raw_record["userIdentity"]["principalId"]

    request_parameters = record.requestParameters
    assert str(request_parameters.sourceIPAddress) == "205.255.255.255/32"
    assert record.responseElements.x_amz_request_id == raw_record["responseElements"]["x-amz-request-id"]
    assert record.responseElements.x_amz_id_2 == raw_record["responseElements"]["x-amz-id-2"]

    s3 = record.s3
    raw_s3 = raw_event["Records"][0]["s3"]
    assert s3.s3SchemaVersion == raw_record["s3"]["s3SchemaVersion"]
    assert s3.configurationId == raw_record["s3"]["configurationId"]
    assert s3.object.key == raw_s3["object"]["key"]
    assert s3.object.size is None
    assert s3.object.eTag is None
    assert s3.object.versionId is None
    assert s3.object.sequencer == raw_s3["object"]["sequencer"]

    bucket = s3.bucket
    raw_bucket = raw_record["s3"]["bucket"]
    assert bucket.name == raw_bucket["name"]
    assert bucket.ownerIdentity.principalId == raw_bucket["ownerIdentity"]["principalId"]
    assert bucket.arn == raw_bucket["arn"]


def test_s3_empty_object():
    raw_event = load_event("s3Event.json")
    raw_event["Records"][0]["s3"]["object"]["size"] = 0
    S3Model(**raw_event)


def test_s3_none_object_size_failed_validation():
    raw_event = load_event("s3Event.json")
    raw_event["Records"][0]["s3"]["object"]["size"] = None
    with pytest.raises(ValidationError):
        S3Model(**raw_event)


def test_s3_none_etag_value_failed_validation():
    raw_event = load_event("s3Event.json")
    raw_event["Records"][0]["s3"]["object"]["eTag"] = None
    with pytest.raises(ValidationError):
        S3Model(**raw_event)
