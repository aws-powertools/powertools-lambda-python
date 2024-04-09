from aws_lambda_powertools.utilities.data_classes import S3Event, SQSEvent, SNSEvent, EventBridgeEvent, KinesisFirehoseEvent
from aws_lambda_powertools.utilities.data_classes.sns_event import SNSMessage
from aws_lambda_powertools.utilities.data_classes.ses_event import SESMessage
from aws_lambda_powertools.utilities.data_classes.cloud_watch_logs_event import CloudWatchLogsLogEvent
import aws_lambda_powertools.utilities.data_classes.nested_test_events as nested_test_events

# TODO: unit tests

def lambda_handler_sqs_s3(event: SQSEvent = nested_test_events.sqs_s3_event): # sqs(s3)
    sqs_event = SQSEvent(event)
    s3_event = sqs_event.decode_nested_events(S3Event)
    for rec in s3_event:
        print('rec:', rec.bucket_name)

def lambda_handler_sqs_s3_single(event: SQSEvent = nested_test_events.sqs_s3_event): # sqs(s3)
    sqs_event = SQSEvent(event)
    s3_event = sqs_event.decode_nested_event(S3Event)
    print('bucket:', s3_event.bucket_name)

def lambda_handler_sqs_sns(event: SQSEvent = nested_test_events.sqs_sns_event): # sqs(sns)
    sqs_event = SQSEvent(event)
    sns_event = sqs_event.decode_nested_events(SNSMessage)
    for rec in sns_event:
        print('rec:', type(rec))
        print(rec.message)


def lambda_handler_sns_s3(event: SNSEvent = nested_test_events.sns_s3_event): # sns(s3)
    sns_event = SNSEvent(event)
    s3_event = sns_event.decode_nested_events(S3Event)
    for rec in s3_event:
        print(type(rec))
        print('rec:', rec.bucket_name)


def lambda_handler_sqs_s3_multi(event: SQSEvent = nested_test_events.sqs_s3_multi_event): # sqs(s3, s3)
    sqs_event = SQSEvent(event)
    s3_event = sqs_event.decode_nested_events(S3Event)
    for rec in s3_event:
        print('rec:', rec.bucket_name)


def lambda_handler_sqs_sns_s3(event: SQSEvent = nested_test_events.sqs_sns_s3_event): # sqs(sns(s3))
    sqs_event = SQSEvent(event)
    sns_event = sqs_event.decode_nested_events(SNSMessage)
    for rec in sns_event:
        print('sns rec:', type(rec), rec)
        print('sns message:', rec.message)

        s3_event = rec.decode_nested_events(S3Event)
        print('s3 rec:', type(s3_event), s3_event)
        print(next(s3_event).bucket_name)


def lambda_handler_sns_ses(event: SNSEvent = nested_test_events.sns_ses_event): # sns(ses)
    sns_event = SNSEvent(event)
    ses_event = sns_event.decode_nested_events(SESMessage)
    for rec in ses_event:
        print('rec:', type(rec), rec)
        print('rec:', rec.get("mail").get('source'))
        # print('rec:', rec.mail) #but can't do rec.mail bc no "SES" key

def lambda_handler_eb_s3(event: EventBridgeEvent = nested_test_events.eb_s3_event): # eventbridge(s3)
    eb_event = EventBridgeEvent(event)
    s3_event = eb_event.decode_nested_events(S3Event)
    for rec in s3_event:
        print('type:', type(rec))
        print('rec:', rec.bucket_name)

def lambda_handler_sqs_eb_s3(event: nested_test_events.sqs_eb_s3_event): # sqs(eventbridge(s3))
    sqs_event = SQSEvent(event)
    for rec in sqs_event:
        eb_event = sqs_event.decode_nested_events(EventBridgeEvent)
        for rec in eb_event:
            print('rec:', type(rec), rec)
            s3_event = rec.decode_nested_events(S3Event)
            for r in s3_event:
                print(type(r))
                print('rec:', r.bucket_name)

def lambda_handler_firehose_sns_event(event = nested_test_events.firehose_sns_event): # firehose(sns)
    firehose_event = KinesisFirehoseEvent(event)
    sns_event = firehose_event.decode_nested_events(SNSEvent)
    #just gives back the encrypted data, so can't cast it into SNSEvent, have to decrypt it and then cast it to get the SNSEvent
    for rec in sns_event:
        print('type:', type(rec), rec)
        print('rec:', rec.sns_message)

def lambda_handler_firehose_cw_event(event = nested_test_events.firehose_cw_event): # firehose(cw)
    firehose_event = KinesisFirehoseEvent(event)
    cw_event = firehose_event.decode_nested_events(CloudWatchLogsLogEvent)
    for rec in cw_event:
        print('type:', type(rec), rec)

lambda_handler_sqs_s3(nested_test_events.sqs_s3_event)
lambda_handler_sqs_s3_single(nested_test_events.sqs_s3_event)
lambda_handler_sqs_sns(nested_test_events.sqs_sns_event)
lambda_handler_sns_s3(nested_test_events.sns_s3_event)
lambda_handler_sqs_s3_multi(nested_test_events.sqs_s3_multi_event)
lambda_handler_sqs_sns_s3(nested_test_events.sqs_sns_s3_event)
lambda_handler_sns_ses(nested_test_events.sns_ses_event) # not being casted correctly bc no "SES" key but works as dict
# lambda_handler_firehose_sns_event(test_events.firehose_sns_event) # just gives back the encrypted data, so can't cast it
# lambda_handler_firehose_cw_event(test_events.firehose_cw_event) # just gives back the encrypted data, so can't cast it
# lambda_handler_eb_s3(test_events.eb_s3_event) #the nested s3 event isn't a full s3 event bc doesn't have a Records key at the top level. so can't call the s3 methods on it
# lambda_handler_sqs_eb_s3(test_events.sqs_eb_s3_event) #same as above
