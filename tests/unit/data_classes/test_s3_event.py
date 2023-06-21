from urllib.parse import quote_plus

from aws_lambda_powertools.utilities.data_classes import S3Event
from tests.functional.utils import load_event


def test_s3_trigger_event():
    raw_event = load_event("s3Event.json")
    parsed_event = S3Event(raw_event)

    records = list(parsed_event.records)
    assert len(records) == 1
    record = records[0]
    assert record.event_version == "2.1"
    assert record.event_source == "aws:s3"
    assert record.aws_region == "us-east-2"
    assert record.event_time == "2019-09-03T19:37:27.192Z"
    assert record.event_name == "ObjectCreated:Put"
    user_identity = record.user_identity
    assert user_identity.principal_id == "AWS:AIDAINPONIXQXHT3IKHL2"
    request_parameters = record.request_parameters
    assert request_parameters.source_ip_address == "205.255.255.255"
    assert record.response_elements["x-amz-request-id"] == "D82B88E5F771F645"
    s3 = record.s3
    assert s3.s3_schema_version == "1.0"
    assert s3.configuration_id == "828aa6fc-f7b5-4305-8584-487c791949c1"
    bucket = s3.bucket
    assert bucket.name == "lambda-artifacts-deafc19498e3f2df"
    assert bucket.owner_identity.principal_id == "A3I5XTEXAMAI3E"
    assert bucket.arn == "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df"
    assert s3.get_object.key == "b21b84d653bb07b05b1e6b33684dc11b"
    assert s3.get_object.size == 1305107
    assert s3.get_object.etag == "b21b84d653bb07b05b1e6b33684dc11b"
    assert s3.get_object.version_id is None
    assert s3.get_object.sequencer == "0C0F6F405D6ED209E1"
    assert record.glacier_event_data is None
    assert parsed_event.record.raw_event == raw_event["Records"][0]
    assert parsed_event.bucket_name == "lambda-artifacts-deafc19498e3f2df"
    assert parsed_event.object_key == "b21b84d653bb07b05b1e6b33684dc11b"


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
                    }
                }
            }
        ]
    }
    event = S3Event(example_event)
    record = next(event.records)
    glacier_event_data = record.glacier_event_data
    assert glacier_event_data is not None
    assert glacier_event_data.restore_event_data.lifecycle_restoration_expiry_time == "1970-01-01T00:01:00.000Z"
    assert glacier_event_data.restore_event_data.lifecycle_restore_storage_class == "standard"


def test_s3_glacier_event_json():
    event = S3Event(load_event("s3EventGlacier.json"))
    glacier_event_data = event.record.glacier_event_data
    assert glacier_event_data is not None
    assert glacier_event_data.restore_event_data.lifecycle_restoration_expiry_time == "1970-01-01T00:01:00.000Z"
    assert glacier_event_data.restore_event_data.lifecycle_restore_storage_class == "standard"
