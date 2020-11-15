import json

import pytest


@pytest.fixture
def schema():
    return {
        "$schema": "http://json-schema.org/draft-07/schema",
        "$id": "http://example.com/example.json",
        "type": "object",
        "title": "Sample schema",
        "description": "The root schema comprises the entire JSON document.",
        "examples": [{"message": "hello world", "username": "lessa"}],
        "required": ["message", "username"],
        "properties": {
            "message": {
                "$id": "#/properties/message",
                "type": "string",
                "title": "The message",
                "examples": ["hello world"],
            },
            "username": {
                "$id": "#/properties/username",
                "type": "string",
                "title": "The username",
                "examples": ["lessa"],
            },
        },
    }


@pytest.fixture
def schema_array():
    return {
        "$schema": "http://json-schema.org/draft-07/schema",
        "$id": "http://example.com/example.json",
        "type": "array",
        "title": "Sample schema",
        "description": "Sample JSON Schema for dummy data in an array",
        "examples": [[{"username": "lessa", "message": "hello world"}]],
        "additionalItems": True,
        "items": {
            "$id": "#/items",
            "anyOf": [
                {
                    "$id": "#/items/anyOf/0",
                    "type": "object",
                    "description": "Dummy data in an array",
                    "required": ["message", "username"],
                    "properties": {
                        "message": {
                            "$id": "#/items/anyOf/0/properties/message",
                            "type": "string",
                            "title": "The message",
                            "examples": ["hello world"],
                        },
                        "username": {
                            "$id": "#/items/anyOf/0/properties/usernam",
                            "type": "string",
                            "title": "The username",
                            "examples": ["lessa"],
                        },
                    },
                }
            ],
        },
    }


@pytest.fixture
def schema_response():
    return {
        "$schema": "http://json-schema.org/draft-07/schema",
        "$id": "http://example.com/example.json",
        "type": "object",
        "title": "Sample outgoing schema",
        "description": "The root schema comprises the entire JSON document.",
        "examples": [{"statusCode": 200, "body": "response"}],
        "required": ["statusCode", "body"],
        "properties": {
            "statusCode": {"$id": "#/properties/statusCode", "type": "integer", "title": "The statusCode"},
            "body": {"$id": "#/properties/body", "type": "string", "title": "The response"},
        },
    }


@pytest.fixture
def raw_event():
    return {"message": "hello hello", "username": "blah blah"}


@pytest.fixture
def wrapped_event():
    return {"data": {"payload": {"message": "hello hello", "username": "blah blah"}}}


@pytest.fixture
def wrapped_event_json_string():
    return {"data": json.dumps({"payload": {"message": "hello hello", "username": "blah blah"}})}


@pytest.fixture
def wrapped_event_base64_json_string():
    return {"data": "eyJtZXNzYWdlIjogImhlbGxvIGhlbGxvIiwgInVzZXJuYW1lIjogImJsYWggYmxhaCJ9="}


@pytest.fixture
def raw_response():
    return {"statusCode": 200, "body": "response"}


@pytest.fixture
def apigateway_event():
    return {
        "body": '{"message": "hello world", "username": "lessa"}',
        "resource": "/{proxy+}",
        "path": "/path/to/resource",
        "httpMethod": "POST",
        "isBase64Encoded": True,
        "queryStringParameters": {"foo": "bar"},
        "multiValueQueryStringParameters": {"foo": ["bar"]},
        "pathParameters": {"proxy": "/path/to/resource"},
        "stageVariables": {"baz": "qux"},
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "en-US,en;q=0.8",
            "Cache-Control": "max-age=0",
            "CloudFront-Forwarded-Proto": "https",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-Mobile-Viewer": "false",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Tablet-Viewer": "false",
            "CloudFront-Viewer-Country": "US",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Custom User Agent String",
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "X-Amz-Cf-Id": "cDehVQoZnx43VYQb9j2-nvCh-9z396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "X-Forwarded-Port": "443",
            "X-Forwarded-Proto": "https",
        },
        "multiValueHeaders": {
            "Accept": ["text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"],
            "Accept-Encoding": ["gzip, deflate, sdch"],
            "Accept-Language": ["en-US,en;q=0.8"],
            "Cache-Control": ["max-age=0"],
            "CloudFront-Forwarded-Proto": ["https"],
            "CloudFront-Is-Desktop-Viewer": ["true"],
            "CloudFront-Is-Mobile-Viewer": ["false"],
            "CloudFront-Is-SmartTV-Viewer": ["false"],
            "CloudFront-Is-Tablet-Viewer": ["false"],
            "CloudFront-Viewer-Country": ["US"],
            "Host": ["0123456789.execute-api.us-east-1.amazonaws.com"],
            "Upgrade-Insecure-Requests": ["1"],
            "User-Agent": ["Custom User Agent String"],
            "Via": ["1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)"],
            "X-Amz-Cf-Id": ["cDehVQoZnx43VYQb9j2-nvCh-9z396Uhbp027Y2JvkCPNLmGJHqlaA=="],
            "X-Forwarded-For": ["127.0.0.1, 127.0.0.2"],
            "X-Forwarded-Port": ["443"],
            "X-Forwarded-Proto": ["https"],
        },
        "requestContext": {
            "accountId": "123456789012",
            "resourceId": "123456",
            "stage": "prod",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "requestTime": "09/Apr/2015:12:34:56 +0000",
            "requestTimeEpoch": 1428582896000,
            "path": "/prod/path/to/resource",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "apiId": "1234567890",
            "protocol": "HTTP/1.1",
        },
    }


@pytest.fixture
def sns_event():
    return {
        "Records": [
            {
                "EventSource": "aws:sns",
                "EventVersion": "1.0",
                "EventSubscriptionArn": "arn:aws:sns:us-east-1::ExampleTopic",
                "Sns": {
                    "Type": "Notification",
                    "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
                    "TopicArn": "arn:aws:sns:us-east-1:123456789012:ExampleTopic",
                    "Subject": "example subject",
                    "Message": '{"message": "hello world", "username": "lessa"}',
                    "Timestamp": "1970-01-01T00:00:00.000Z",
                    "SignatureVersion": "1",
                    "Signature": "EXAMPLE",
                    "SigningCertUrl": "https://www.example.com",
                    "UnsubscribeUrl": "https://www.example.com",
                    "MessageAttributes": {
                        "Test": {"Type": "String", "Value": "TestString"},
                        "TestBinary": {"Type": "Binary", "Value": "TestBinary"},
                    },
                },
            }
        ]
    }


@pytest.fixture
def kinesis_event():
    return {
        "Records": [
            {
                "kinesis": {
                    "partitionKey": "partitionKey-03",
                    "kinesisSchemaVersion": "1.0",
                    "data": "eyJtZXNzYWdlIjogImhlbGxvIGhlbGxvIiwgInVzZXJuYW1lIjogImJsYWggYmxhaCJ9=",
                    "sequenceNumber": "49545115243490985018280067714973144582180062593244200961",
                    "approximateArrivalTimestamp": 1428537600.0,
                },
                "eventSource": "aws:kinesis",
                "eventID": "shardId-000000000000:49545115243490985018280067714973144582180062593244200961",
                "invokeIdentityArn": "arn:aws:iam::EXAMPLE",
                "eventVersion": "1.0",
                "eventName": "aws:kinesis:record",
                "eventSourceARN": "arn:aws:kinesis:EXAMPLE",
                "awsRegion": "us-east-1",
            }
        ]
    }


@pytest.fixture
def eventbridge_event():
    return {
        "id": "cdc73f9d-aea9-11e3-9d5a-835b769c0d9c",
        "detail-type": "Scheduled Event",
        "source": "aws.events",
        "account": "123456789012",
        "time": "1970-01-01T00:00:00Z",
        "region": "us-east-1",
        "resources": ["arn:aws:events:us-east-1:123456789012:rule/ExampleRule"],
        "detail": {"message": "hello hello", "username": "blah blah"},
    }


@pytest.fixture
def sqs_event():
    return {
        "Records": [
            {
                "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
                "receiptHandle": "MessageReceiptHandle",
                "body": '{"message": "hello world", "username": "lessa"}',
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1523232000000",
                    "SenderId": "123456789012",
                    "ApproximateFirstReceiveTimestamp": "1523232000001",
                },
                "messageAttributes": {},
                "md5OfBody": "7b270e59b47ff90a553787216d55d91d",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
                "awsRegion": "us-east-1",
            },
        ]
    }


@pytest.fixture
def cloudwatch_logs_event():
    return {
        "awslogs": {
            "data": "H4sIACZAXl8C/52PzUrEMBhFX2UILpX8tPbHXWHqIOiq3Q1F0ubrWEiakqTWofTdTYYB0YWL2d5zvnuTFellBIOedoiyKH5M0iwnlKH7HZL6dDB6ngLDfLFYctUKjie9gHFaS/sAX1xNEq525QxwFXRGGMEkx4Th491rUZdV3YiIZ6Ljfd+lfSyAtZloacQgAkqSJCGhxM6t7cwwuUGPz4N0YKyvO6I9WDeMPMSo8Z4Ca/kJ6vMEYW5f1MX7W1lVxaG8vqX8hNFdjlc0iCBBSF4ERT/3Pl7RbMGMXF2KZMh/C+gDpNS7RRsp0OaRGzx0/t8e0jgmcczyLCWEePhni/23JWalzjdu0a3ZvgEaNLXeugEAAA=="  # noqa: E501
        }
    }


@pytest.fixture
def cloudwatch_logs_schema():
    return {
        "$schema": "http://json-schema.org/draft-07/schema",
        "$id": "http://example.com/example.json",
        "type": "array",
        "title": "Sample schema",
        "description": "Sample JSON Schema for CloudWatch Logs logEvents using structured dummy data",
        "examples": [
            [
                {
                    "id": "eventId1",
                    "message": {"username": "lessa", "message": "hello world"},
                    "timestamp": 1440442987000,
                },
                {
                    "id": "eventId2",
                    "message": {"username": "dummy", "message": "hello world"},
                    "timestamp": 1440442987001,
                },
            ]
        ],
        "additionalItems": True,
        "items": {
            "$id": "#/items",
            "anyOf": [
                {
                    "$id": "#/items/anyOf/0",
                    "type": "object",
                    "title": "The first anyOf schema",
                    "description": "Actual log data found in CloudWatch Logs logEvents key",
                    "required": ["id", "message", "timestamp"],
                    "properties": {
                        "id": {
                            "$id": "#/items/anyOf/0/properties/id",
                            "type": "string",
                            "title": "The id schema",
                            "description": "Unique identifier for log event",
                            "default": "",
                            "examples": ["eventId1"],
                        },
                        "message": {
                            "$id": "#/items/anyOf/0/properties/message",
                            "type": "object",
                            "title": "The message schema",
                            "description": "Log data captured in CloudWatch Logs",
                            "default": {},
                            "examples": [{"username": "lessa", "message": "hello world"}],
                            "required": ["username", "message"],
                            "properties": {
                                "username": {
                                    "$id": "#/items/anyOf/0/properties/message/properties/username",
                                    "type": "string",
                                    "title": "The username",
                                    "examples": ["lessa"],
                                },
                                "message": {
                                    "$id": "#/items/anyOf/0/properties/message/properties/message",
                                    "type": "string",
                                    "title": "The message",
                                    "examples": ["hello world"],
                                },
                            },
                            "additionalProperties": True,
                        },
                        "timestamp": {
                            "$id": "#/items/anyOf/0/properties/timestamp",
                            "type": "integer",
                            "title": "The timestamp schema",
                            "description": "Log event epoch timestamp in milliseconds",
                            "default": 0,
                            "examples": [1440442987000],
                        },
                    },
                }
            ],
        },
    }
