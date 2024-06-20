from urllib.parse import quote_plus

from aws_lambda_powertools.utilities.data_classes import S3Event
from tests.functional.utils import load_event


def test_s3_trigger_event():
    raw_event = load_event("s3Event.json")
    parsed_event = S3Event(raw_event)

    records = list(parsed_event.records)
    assert len(records) == 1
    record = records[0]
    record_raw = raw_event["Records"][0]

    assert record.event_version == record_raw["eventVersion"]
    assert record.event_source == record_raw["eventSource"]
    assert record.aws_region == record_raw["awsRegion"]
    assert record.event_time == record_raw["eventTime"]
    assert record.event_name == record_raw["eventName"]
    user_identity = record.user_identity
    assert user_identity.principal_id == raw_event["Records"][0]["userIdentity"]["principalId"]
    request_parameters = record.request_parameters
    assert request_parameters.source_ip_address == raw_event["Records"][0]["requestParameters"]["sourceIPAddress"]
    assert (
        record.response_elements.get("x-amz-request-id")
        == raw_event["Records"][0]["responseElements"]["x-amz-request-id"]
    )
    s3 = record.s3
    s3_raw = raw_event["Records"][0]["s3"]
    assert s3.get_object.key == s3_raw["object"]["key"]
    assert s3.get_object.size == s3_raw["object"]["size"]
    assert s3.get_object.etag == s3_raw["object"]["eTag"]
    assert s3.get_object.version_id is None
    assert s3.get_object.sequencer == s3_raw["object"]["sequencer"]
    assert s3.s3_schema_version == s3_raw["s3SchemaVersion"]
    assert s3.configuration_id == s3_raw["configurationId"]

    bucket = s3.bucket
    bucket_raw = raw_event["Records"][0]["s3"]["bucket"]
    assert bucket.name == bucket_raw["name"]
    assert bucket.owner_identity.principal_id == bucket_raw["ownerIdentity"]["principalId"]
    assert bucket.arn == bucket_raw["arn"]

    assert record.glacier_event_data is None
    assert parsed_event.record.raw_event == raw_event["Records"][0]
    assert parsed_event.bucket_name == bucket_raw["name"]
    assert parsed_event.object_key == s3_raw["object"]["key"]


def test_s3_key_unquote_plus():
    tricky_name = "foo name+value"
    event_dict = {"Records": [{"s3": {"object": {"key": quote_plus(tricky_name)}}}]}
    event = S3Event(event_dict)
    assert event.object_key == tricky_name


def test_s3_key_url_decoded_key():
    raw_event = load_event("s3EventDecodedKey.json")
    parsed_event = S3Event(raw_event)
    assert parsed_event.object_key == raw_event["Records"][0]["s3"]["object"]["urlDecodedKey"]


def test_s3_glacier_event():
    example_event = {
        "Records": [
            {
                "glacierEventData": {
                    "restoreEventData": {
                        "lifecycleRestorationExpiryTime": "1970-01-01T00:01:00.000Z",
                        "lifecycleRestoreStorageClass": "standard",
                    },
                },
            },
        ],
    }
    event = S3Event(example_event)
    record = next(event.records)
    glacier_event_data = record.glacier_event_data
    assert glacier_event_data is not None
    assert glacier_event_data.restore_event_data.lifecycle_restoration_expiry_time == "1970-01-01T00:01:00.000Z"
    assert glacier_event_data.restore_event_data.lifecycle_restore_storage_class == "standard"


def test_s3_glacier_event_json():
    raw_event = load_event("s3EventGlacier.json")
    parsed_event = S3Event(raw_event)

    glacier_event_data = parsed_event.record.glacier_event_data
    glacier_event_data_raw = raw_event["Records"][0]["glacierEventData"]
    assert glacier_event_data is not None
    assert (
        glacier_event_data.restore_event_data.lifecycle_restoration_expiry_time
        == glacier_event_data_raw["restoreEventData"]["lifecycleRestorationExpiryTime"]
    )
    assert (
        glacier_event_data.restore_event_data.lifecycle_restore_storage_class
        == glacier_event_data_raw["restoreEventData"]["lifecycleRestoreStorageClass"]
    )
