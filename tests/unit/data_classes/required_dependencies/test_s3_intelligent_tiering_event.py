from aws_lambda_powertools.utilities.data_classes import S3Event
from tests.functional.utils import load_event


def test_s3_intelligent_tiering_event():
    """Test S3 IntelligentTiering event with get_object field"""
    event = S3Event(load_event("s3EventIntelligentTiering.json"))

    # Test first record
    record = event.record
    assert record.event_name == "IntelligentTiering"
    assert record.event_version == "2.3"
    assert record.event_source == "aws:s3"
    assert record.aws_region == "ap-southeast-2"

    # Test user identity
    assert record.user_identity.principal_id == "s3.amazonaws.com"

    # Test S3 object via get_object property (handles both 'object' and 'get_object' keys)
    s3_object = record.s3.get_object
    assert s3_object.key == "myobject"
    assert s3_object.size == 252294
    assert s3_object.etag == "4e9270240d7d62d5ee8dbfcb7a7a3279"
    assert s3_object.version_id == "tiogA9Ga7Xi49yfJ6lkeTxPYx7ZK75yn"
    assert s3_object.sequencer == "0066A8D0E77DE42BC5"

    # Test bucket
    assert record.s3.bucket.name == "mybucket"
    assert record.s3.bucket.arn == "arn:aws:s3:::mybucket"

    # Test intelligentTieringEventData
    assert record.intelligent_tiering_event_data is not None
    assert record.intelligent_tiering_event_data.destination_access_tier == "ARCHIVE_ACCESS"

    # Verify glacierEventData is None
    assert record.glacier_event_data is None

    # Test convenience properties
    assert event.bucket_name == "mybucket"
    assert event.object_key == "myobject"


def test_s3_intelligent_tiering_event_iteration():
    """Test iterating through multiple IntelligentTiering records"""
    event = S3Event(load_event("s3EventIntelligentTiering.json"))

    records = list(event.records)
    assert len(records) == 1

    for record in event.records:
        assert record.event_name == "IntelligentTiering"
        assert record.s3.get_object.key == "myobject"
        assert record.intelligent_tiering_event_data.destination_access_tier == "ARCHIVE_ACCESS"


def test_s3_intelligent_tiering_deep_archive_access():
    """Test IntelligentTiering event with DEEP_ARCHIVE_ACCESS tier"""
    raw_event = load_event("s3EventIntelligentTiering.json")
    raw_event["Records"][0]["intelligentTieringEventData"]["destinationAccessTier"] = "DEEP_ARCHIVE_ACCESS"

    event = S3Event(raw_event)
    record = event.record

    assert record.intelligent_tiering_event_data.destination_access_tier == "DEEP_ARCHIVE_ACCESS"
