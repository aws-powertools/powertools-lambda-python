from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.parser.models import S3Model, S3RecordModel
from aws_lambda_powertools.utilities.typing import LambdaContext
from tests.functional.parser.utils import load_event


@event_parser(model=S3Model)
def handle_s3(event: S3Model, _: LambdaContext):
    records = list(event.Records)
    assert len(records) == 1
    record: S3RecordModel = records[0]
    assert record.eventVersion == "2.1"
    assert record.eventSource == "aws:s3"
    assert record.awsRegion == "us-east-2"
    convert_time = int(round(record.eventTime.timestamp() * 1000))
    assert convert_time == 1567539447192
    assert record.eventName == "ObjectCreated:Put"
    user_identity = record.userIdentity
    assert user_identity.principalId == "AWS:AIDAINPONIXQXHT3IKHL2"
    request_parameters = record.requestParameters
    assert str(request_parameters.sourceIPAddress) == "205.255.255.255/32"
    assert record.responseElements.x_amz_request_id == "D82B88E5F771F645"
    assert (
        record.responseElements.x_amz_id_2
        == "vlR7PnpV2Ce81l0PRw6jlUpck7Jo5ZsQjryTjKlc5aLWGVHPZLj5NeC6qMa0emYBDXOo6QBU0Wo="
    )
    s3 = record.s3
    assert s3.s3SchemaVersion == "1.0"
    assert s3.configurationId == "828aa6fc-f7b5-4305-8584-487c791949c1"
    bucket = s3.bucket
    assert bucket.name == "lambda-artifacts-deafc19498e3f2df"
    assert bucket.ownerIdentity.principalId == "A3I5XTEXAMAI3E"
    assert bucket.arn == "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df"
    assert s3.object.key == "b21b84d653bb07b05b1e6b33684dc11b"
    assert s3.object.size == 1305107
    assert s3.object.eTag == "b21b84d653bb07b05b1e6b33684dc11b"
    assert s3.object.versionId is None
    assert s3.object.sequencer == "0C0F6F405D6ED209E1"
    assert record.glacierEventData is None


@event_parser(model=S3Model)
def handle_s3_glacier(event: S3Model, _: LambdaContext):
    records = list(event.Records)
    assert len(records) == 1
    record: S3RecordModel = records[0]
    assert record.eventVersion == "2.1"
    assert record.eventSource == "aws:s3"
    assert record.awsRegion == "us-east-2"
    convert_time = int(round(record.eventTime.timestamp() * 1000))
    assert convert_time == 1567539447192
    assert record.eventName == "ObjectCreated:Put"
    user_identity = record.userIdentity
    assert user_identity.principalId == "AWS:AIDAINPONIXQXHT3IKHL2"
    request_parameters = record.requestParameters
    assert str(request_parameters.sourceIPAddress) == "205.255.255.255/32"
    assert record.responseElements.x_amz_request_id == "D82B88E5F771F645"
    assert (
        record.responseElements.x_amz_id_2
        == "vlR7PnpV2Ce81l0PRw6jlUpck7Jo5ZsQjryTjKlc5aLWGVHPZLj5NeC6qMa0emYBDXOo6QBU0Wo="
    )
    s3 = record.s3
    assert s3.s3SchemaVersion == "1.0"
    assert s3.configurationId == "828aa6fc-f7b5-4305-8584-487c791949c1"
    bucket = s3.bucket
    assert bucket.name == "lambda-artifacts-deafc19498e3f2df"
    assert bucket.ownerIdentity.principalId == "A3I5XTEXAMAI3E"
    assert bucket.arn == "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df"
    assert s3.object.key == "b21b84d653bb07b05b1e6b33684dc11b"
    assert s3.object.size == 1305107
    assert s3.object.eTag == "b21b84d653bb07b05b1e6b33684dc11b"
    assert s3.object.versionId is None
    assert s3.object.sequencer == "0C0F6F405D6ED209E1"
    assert record.glacierEventData is not None
    convert_time = int(
        round(record.glacierEventData.restoreEventData.lifecycleRestorationExpiryTime.timestamp() * 1000)
    )
    assert convert_time == 60000
    assert record.glacierEventData.restoreEventData.lifecycleRestoreStorageClass == "standard"


def test_s3_trigger_event():
    event_dict = load_event("s3Event.json")
    handle_s3(event_dict, LambdaContext())


def test_s3_glacier_trigger_event():
    event_dict = load_event("s3EventGlacier.json")
    handle_s3_glacier(event_dict, LambdaContext())
