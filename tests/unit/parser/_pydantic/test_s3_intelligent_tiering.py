from aws_lambda_powertools.utilities.parser.models import S3Model, S3RecordModel
from tests.functional.utils import load_event


def test_s3_intelligent_tiering_event():
    """Test parsing of S3 IntelligentTiering events with get_object field"""
    raw_event = load_event("s3EventIntelligentTiering.json")
    parsed_event: S3Model = S3Model(**raw_event)

    records = list(parsed_event.Records)
    assert len(records) == 1

    record: S3RecordModel = records[0]
    raw_record = raw_event["Records"][0]

    # Verify basic event properties
    assert record.eventVersion == "2.3"
    assert record.eventSource == "aws:s3"
    assert record.awsRegion == "ap-southeast-2"
    assert record.eventName == "IntelligentTiering"

    # Verify user identity
    user_identity = record.userIdentity
    assert user_identity.principalId == "s3.amazonaws.com"

    # Verify request parameters
    request_parameters = record.requestParameters
    # Note: sourceIPAddress is "s3.amazonaws.com" for IntelligentTiering events, not an IP
    assert str(request_parameters.sourceIPAddress) == "s3.amazonaws.com"

    # Verify response elements
    assert record.responseElements.x_amz_request_id == raw_record["responseElements"]["x-amz-request-id"]
    assert record.responseElements.x_amz_id_2 == raw_record["responseElements"]["x-amz-id-2"]

    # Verify S3 message
    s3 = record.s3
    assert s3.s3SchemaVersion == raw_record["s3"]["s3SchemaVersion"]
    assert s3.configurationId == raw_record["s3"]["configurationId"]

    # Verify bucket
    bucket = s3.bucket
    raw_bucket = raw_record["s3"]["bucket"]
    assert bucket.name == "mybucket"
    assert bucket.ownerIdentity.principalId == raw_bucket["ownerIdentity"]["principalId"]
    assert bucket.arn == "arn:aws:s3:::mybucket"

    # Verify get_object field (IntelligentTiering uses 'get_object' instead of 'object')
    assert s3.get_object is not None
    assert s3.get_object.key == "myobject"
    assert s3.get_object.size == 252294
    assert s3.get_object.eTag == "4e9270240d7d62d5ee8dbfcb7a7a3279"
    assert s3.get_object.versionId == "tiogA9Ga7Xi49yfJ6lkeTxPYx7ZK75yn"
    assert s3.get_object.sequencer == "0066A8D0E77DE42BC5"

    # Verify intelligentTieringEventData
    assert record.intelligentTieringEventData is not None
    assert record.intelligentTieringEventData.destinationAccessTier == "ARCHIVE_ACCESS"

    # Verify glacierEventData is None for IntelligentTiering events
    assert record.glacierEventData is None


def test_s3_intelligent_tiering_event_access_tiers():
    """Test different access tier values for IntelligentTiering events"""
    raw_event = load_event("s3EventIntelligentTiering.json")

    # Test ARCHIVE_ACCESS tier (from the test event)
    parsed_event: S3Model = S3Model(**raw_event)
    record = list(parsed_event.Records)[0]
    assert record.intelligentTieringEventData.destinationAccessTier == "ARCHIVE_ACCESS"

    # Test DEEP_ARCHIVE_ACCESS tier
    raw_event["Records"][0]["intelligentTieringEventData"]["destinationAccessTier"] = "DEEP_ARCHIVE_ACCESS"
    parsed_event: S3Model = S3Model(**raw_event)
    record = list(parsed_event.Records)[0]
    assert record.intelligentTieringEventData.destinationAccessTier == "DEEP_ARCHIVE_ACCESS"
