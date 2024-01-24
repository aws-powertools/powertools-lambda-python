import json

from aws_lambda_powertools.utilities.data_classes import S3Event, SQSEvent
# from aws_lambda_powertools.utilities.data_classes.sns_event import SNSMessage
from aws_lambda_powertools.utilities.data_classes import event_source


# @event_source(data_class=SQSEvent)
def lambda_handler(event: SQSEvent, context):
    event = SQSEvent(event)
    nesteds3event = event.decode_nested_events(S3Event)
    for record in event.records: #then how would a for loop work..
        nested_event = record.decode_nested_event(S3Event) #for loop must be for same events inside one event
        print(nested_event, nested_event)

    # event = SQSEvent()
    # sns_events = event.decode_nested_events(Iterator[SNSEvent])
    # for sns_event in sns_events:
    #     s3_events = sns_event.decode_nested_events(S3Event)
    #     for s3_event in s3_events:
    #         print(s3_event.bucket.name)




event = SQSEvent({
    "Records": [
        {
            "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
            "receiptHandle": "MessageReceiptHandle",
            "body": {
                "Message": "{\"Records\":[{\"eventVersion\":\"2.1\",\"eventSource\":\"aws:s3\",\"awsRegion\":\"us-east-1\",\"eventTime\":\"2023-01-01T00:00:00.000Z\",\"eventName\":\"ObjectCreated:Put\",\"userIdentity\":{\"principalId\":\"AWS:123456789012:example-user\"},\"requestParameters\":{\"sourceIPAddress\":\"127.0.0.1\"},\"responseElements\":{\"x-amz-request-id\":\"example-request-id\",\"x-amz-id-2\":\"example-id\"},\"s3\":{\"s3SchemaVersion\":\"1.0\",\"configurationId\":\"testConfigRule\",\"bucket\":{\"name\":\"example-bucket\",\"ownerIdentity\":{\"principalId\":\"EXAMPLE\"},\"arn\":\"arn:aws:s3:::example-bucket\"},\"object\":{\"key\":\"example-object.txt\",\"size\":1024,\"eTag\":\"example-tag\",\"versionId\":\"1\",\"sequencer\":\"example-sequencer\"}}}]}"
            },
            "attributes": {
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1523232000000",
                "SenderId": "123456789012",
                "ApproximateFirstReceiveTimestamp": "1523232000001"
            },
            "messageAttributes": {},
            "md5OfBody": "7b270e59b47ff90a553787216d55d91d",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
            "awsRegion": "us-east-1"
        }
  ]
})

lambda_handler(event, {})
