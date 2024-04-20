from aws_lambda_powertools.utilities.data_classes import S3Event, SQSEvent, SNSEvent, EventBridgeEvent, KinesisFirehoseEvent
from aws_lambda_powertools.utilities.data_classes.sns_event import SNSMessage
from aws_lambda_powertools.utilities.data_classes.ses_event import SESEventRecord
from aws_lambda_powertools.utilities.data_classes.s3_event import S3EventBridgeNotificationDetail
import aws_lambda_powertools.utilities.data_classes.nested_test_events as nested_test_events

def test_sqs_s3(): # sqs(s3)
    raw_event = nested_test_events.sqs_s3_event
    parsed_event = SQSEvent(raw_event)

    records = list(parsed_event.records)
    assert len(records) == 1
    record = records[0]
    record_raw = raw_event["Records"][0]
    assert record.aws_region == record_raw["awsRegion"]

    s3_event = parsed_event.decode_nested_events(S3Event)
    for rec in s3_event:
        assert rec.bucket_name == "sqs-s3-unwrap-bucket-683517028648"

def test_sqs_s3_single(): # sqs(s3)
    raw_event = nested_test_events.sqs_s3_event
    parsed_event = SQSEvent(raw_event)

    s3_event = parsed_event.decode_nested_event(S3Event)
    assert s3_event.bucket_name == "sqs-s3-unwrap-bucket-683517028648"

def test_sqs_sns(): # sqs(sns)
    raw_event = nested_test_events.sqs_sns_event
    parsed_event = SQSEvent(raw_event)

    sns_event = parsed_event.decode_nested_events(SNSMessage)
    for rec in sns_event:
        assert rec.message == "from sns"

def test_sns_s3(): # sns(s3)
    raw_event = nested_test_events.sns_s3_event
    parsed_event = SNSEvent(raw_event)

    s3_event = parsed_event.decode_nested_events(S3Event)
    for rec in s3_event:
        assert rec.bucket_name == "s3-sns-unwrap-bucket-683517028648"

def test_sqs_s3_multiple_events(): # sqs(s3, s3)
    raw_event = nested_test_events.sqs_s3_multi_event
    parsed_event = SQSEvent(raw_event)

    s3_event = parsed_event.decode_nested_events(S3Event)
    for rec in s3_event:
        print('sqs_s3_multi_event bucket:', rec.bucket_name) #TODO:

def test_sqs_sns_s3_direct(): # sqs(sns(s3))
    raw_event = nested_test_events.sqs_sns_s3_event
    parsed_event = SQSEvent(raw_event)

    sns_event = parsed_event.decode_nested_event(SNSMessage)
    s3_event = sns_event.decode_nested_event(S3Event)
    assert s3_event.bucket_name == "unwraptestevents-bucket-683517028648"

def test_sqs_sns_s3(): # sqs(sns(s3))
    raw_event = nested_test_events.sqs_sns_s3_event
    parsed_event = SQSEvent(raw_event)

    sns_event = parsed_event.decode_nested_events(SNSMessage)
    for rec in sns_event:
        s3_event = rec.decode_nested_events(S3Event)
        for r in s3_event:
            assert r.bucket_name == "unwraptestevents-bucket-683517028648"

def test_sns_ses(): # sns(ses)
    raw_event = nested_test_events.sns_ses_event
    parsed_event = SNSEvent(raw_event)
    ses_event = parsed_event.decode_nested_events(SESEventRecord)
    for rec in ses_event:
        assert rec.get("mail").get('source') == "seshub@amazon.com"
        # print('rec:', rec.mail) #but can't do rec.mail bc no "SES" key

def test_eb_s3(): # eventbridge(s3)
    raw_event = nested_test_events.eb_s3_event
    parsed_event = EventBridgeEvent(raw_event)
    s3_event = parsed_event.decode_nested_events(S3EventBridgeNotificationDetail)
    for rec in s3_event:
        assert rec.bucket.name == "s3-eb-unwrap-sourcebucket-7mop1gqlyrzu"


def test_sqs_eb_s3(): # sqs(eventbridge(s3))
    raw_event = nested_test_events.sqs_eb_s3_event
    parsed_event = SQSEvent(raw_event)

    eb_event = parsed_event.decode_nested_events(EventBridgeEvent)
    for rec in eb_event:
        s3_event = rec.decode_nested_events(S3EventBridgeNotificationDetail)
        for r in s3_event:
            assert r.bucket.name == "s3-eb-unwrap-sourcebucket-7mop1gqlyrzu"

def test_firehose_sns_event(event = nested_test_events.firehose_sns_event): # firehose(sns)
    raw_event = nested_test_events.firehose_sns_event
    parsed_event = KinesisFirehoseEvent(raw_event)

    sns_event = parsed_event.decode_nested_events(SNSMessage) #TODO: add a flag to auto decode?
    for rec in sns_event:
        assert rec.message == "message from sns"

def test_firehose_cw_event(): # firehose(cw)
    raw_event = nested_test_events.firehose_cw_event
    parsed_event = KinesisFirehoseEvent(raw_event)

    # cw_event = parsed_event.decode_nested_events(CloudWatchLogsLogEvent) #TODO: gives back encrypted data, and can't be decoded w b64
    # for rec in cw_event:
    #     print('type:', type(rec), rec)
