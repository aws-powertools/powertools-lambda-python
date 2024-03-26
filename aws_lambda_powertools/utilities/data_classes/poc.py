from typing import Iterator
import json
from aws_lambda_powertools.utilities.data_classes import S3Event, SQSEvent, SNSEvent, SESEvent, EventBridgeEvent
import test_events


def lambda_handler_sqs_s3(event: SQSEvent = test_events.sqs_s3_event): # sqs(s3)
    sqs_event = SQSEvent(event)
    s3_event = sqs_event.decode_nested_events(S3Event)
    for rec in s3_event:
        print('rec:', rec.bucket_name)
    # for sqs_record in sqs_event.records:
    #     # print('body in main:', sqs_record.body)
    #     # s3_event = sqs_event.decode_nested_events(Iterator[S3Event]) # is this correct format?
    #     s3_event = sqs_event.decode_nested_events(S3Event)
    #     for rec in s3_event:
    #         print('rec:', rec.bucket_name)
      # print(next(s3_event).bucket_name) # use this if not inside a for loop


def lambda_handler_sqs_sns(event: SQSEvent = test_events.sqs_sns_event): # sqs(sns)
    sqs_event = SQSEvent(event)
    sns_event = sqs_event.decode_nested_events(SNSEvent)
    for rec in sns_event:
        print('rec:', type(rec), rec.sns_message)


def lambda_handler_sns_s3(event: SNSEvent = test_events.sns_s3_event): # sns(s3)
    sns_event = SNSEvent(event)
    s3_event = sns_event.decode_nested_events(S3Event)
    for rec in s3_event:
        print(type(rec))
        print('rec:', rec.bucket_name)


def lambda_handler_sqs_s3_multi(event: SQSEvent = test_events.sqs_s3_multi_event): # sqs(s3, s3)
    sqs_event = SQSEvent(event)
    s3_event = sqs_event.decode_nested_events(S3Event)
    for rec in s3_event:
        print('rec:', rec.bucket_name)


def lambda_handler_sqs_sns_s3(event: SQSEvent = test_events.sqs_sns_s3_event): # sqs(sns(s3))
    sqs_event = SQSEvent(event)
    sns_event = sqs_event.decode_nested_events(SNSEvent)
    for rec in sns_event:
        print('rec:', type(rec), rec.sns_message)
    # s3_event = sns_event.decode_nested_events(S3Event)


def lambda_handler_sns_ses(event: SNSEvent = test_events.sns_ses_event): # sns(ses)
    sns_event = SNSEvent(event)
    ses_event = sns_event.decode_nested_events(SESEvent)
    for rec in ses_event:
        print(type(rec))
        print('rec:', rec.get("mail").get('source')) #but can't do rec.mail bc no "Records" key..

def lambda_handler_eb_s3(event: EventBridgeEvent = test_events.eb_s3_event): # eventbridge(s3)
    eb_event = EventBridgeEvent(event)
    s3_event = eb_event.decode_nested_events(S3Event)
    for rec in s3_event:
        print(type(rec))
        print('rec:', rec)

lambda_handler_sqs_s3(test_events.sqs_s3_event)
# lambda_handler_sqs_sns(test_events.sqs_sns_event) #not working bc sns doesn't have Records key
lambda_handler_sns_s3(test_events.sns_s3_event)
lambda_handler_sqs_s3_multi(test_events.sqs_s3_multi_event)
# lambda_handler_sqs_sns_s3(test_events.sqs_sns_s3_event) #not working bc sns doesn't have Records key
lambda_handler_sns_ses(test_events.sns_ses_event)
# lambda_handler_eb_s3(test_events.eb_s3_event) #EB returning a str, not dict
