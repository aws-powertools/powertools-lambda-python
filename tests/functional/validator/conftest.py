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
def eventbridge_cloudtrail_s3_head_object_event():
    return {
        "account": "123456789012",
        "detail": {
            "additionalEventData": {
                "AuthenticationMethod": "AuthHeader",
                "CipherSuite": "ECDHE-RSA-AES128-GCM-SHA256",
                "SignatureVersion": "SigV4",
                "bytesTransferredIn": 0,
                "bytesTransferredOut": 0,
                "x-amz-id-2": "ejUr9Nd/4IO1juF/a6GOcu+PKrVX6dOH6jDjQOeCJvtARUqzxrhHGrhEt04cqYtAZVqcSEXYqo0=",
            },
            "awsRegion": "us-west-1",
            "eventCategory": "Data",
            "eventID": "be4fdb30-9508-4984-b071-7692221899ae",
            "eventName": "HeadObject",
            "eventSource": "s3.amazonaws.com",
            "eventTime": "2020-12-22T10:05:29Z",
            "eventType": "AwsApiCall",
            "eventVersion": "1.07",
            "managementEvent": False,
            "readOnly": True,
            "recipientAccountId": "123456789012",
            "requestID": "A123B1C123D1E123",
            "requestParameters": {
                "Host": "lambda-artifacts-deafc19498e3f2df.s3.us-west-1.amazonaws.com",
                "bucketName": "lambda-artifacts-deafc19498e3f2df",
                "key": "path1/path2/path3/file.zip",
            },
            "resources": [
                {
                    "ARN": "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df/path1/path2/path3/file.zip",
                    "type": "AWS::S3::Object",
                },
                {
                    "ARN": "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df",
                    "accountId": "123456789012",
                    "type": "AWS::S3::Bucket",
                },
            ],
            "responseElements": None,
            "sourceIPAddress": "AWS Internal",
            "userAgent": "AWS Internal",
            "userIdentity": {
                "accessKeyId": "ABCDEFGHIJKLMNOPQR12",
                "accountId": "123456789012",
                "arn": "arn:aws:sts::123456789012:assumed-role/role-name1/1234567890123",
                "invokedBy": "AWS Internal",
                "principalId": "ABCDEFGHIJKLMN1OPQRST:1234567890123",
                "sessionContext": {
                    "attributes": {"creationDate": "2020-12-09T09:58:24Z", "mfaAuthenticated": "false"},
                    "sessionIssuer": {
                        "accountId": "123456789012",
                        "arn": "arn:aws:iam::123456789012:role/role-name1",
                        "principalId": "ABCDEFGHIJKLMN1OPQRST",
                        "type": "Role",
                        "userName": "role-name1",
                    },
                },
                "type": "AssumedRole",
            },
            "vpcEndpointId": "vpce-a123cdef",
        },
        "detail-type": "AWS API Call via CloudTrail",
        "id": "e0bad426-0a70-4424-b53a-eb902ebf5786",
        "region": "us-west-1",
        "resources": [],
        "source": "aws.s3",
        "time": "2020-12-22T10:05:29Z",
        "version": "0",
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


@pytest.fixture
def eventbridge_schema_registry_cloudtrail_v2_s3():
    return {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {
            "AWSAPICallViaCloudTrail": {
                "properties": {
                    "additionalEventData": {"$ref": "#/definitions/AdditionalEventData"},
                    "awsRegion": {"type": "string"},
                    "errorCode": {"type": "string"},
                    "errorMessage": {"type": "string"},
                    "eventID": {"type": "string"},
                    "eventName": {"type": "string"},
                    "eventSource": {"type": "string"},
                    "eventTime": {"format": "date-time", "type": "string"},
                    "eventType": {"type": "string"},
                    "eventVersion": {"type": "string"},
                    "recipientAccountId": {"type": "string"},
                    "requestID": {"type": "string"},
                    "requestParameters": {"$ref": "#/definitions/RequestParameters"},
                    "resources": {"items": {"type": "object"}, "type": "array"},
                    "responseElements": {"type": ["object", "null"]},
                    "sourceIPAddress": {"type": "string"},
                    "userAgent": {"type": "string"},
                    "userIdentity": {"$ref": "#/definitions/UserIdentity"},
                    "vpcEndpointId": {"type": "string"},
                    "x-amazon-open-api-schema-readOnly": {"type": "boolean"},
                },
                "required": [
                    "eventID",
                    "awsRegion",
                    "eventVersion",
                    "responseElements",
                    "sourceIPAddress",
                    "eventSource",
                    "requestParameters",
                    "resources",
                    "userAgent",
                    "readOnly",
                    "userIdentity",
                    "eventType",
                    "additionalEventData",
                    "vpcEndpointId",
                    "requestID",
                    "eventTime",
                    "eventName",
                    "recipientAccountId",
                ],
                "type": "object",
            },
            "AdditionalEventData": {
                "properties": {
                    "objectRetentionInfo": {"$ref": "#/definitions/ObjectRetentionInfo"},
                    "x-amz-id-2": {"type": "string"},
                },
                "required": ["x-amz-id-2"],
                "type": "object",
            },
            "Attributes": {
                "properties": {
                    "creationDate": {"format": "date-time", "type": "string"},
                    "mfaAuthenticated": {"type": "string"},
                },
                "required": ["mfaAuthenticated", "creationDate"],
                "type": "object",
            },
            "LegalHoldInfo": {
                "properties": {
                    "isUnderLegalHold": {"type": "boolean"},
                    "lastModifiedTime": {"format": "int64", "type": "integer"},
                },
                "type": "object",
            },
            "ObjectRetentionInfo": {
                "properties": {
                    "legalHoldInfo": {"$ref": "#/definitions/LegalHoldInfo"},
                    "retentionInfo": {"$ref": "#/definitions/RetentionInfo"},
                },
                "type": "object",
            },
            "RequestParameters": {
                "properties": {
                    "bucketName": {"type": "string"},
                    "key": {"type": "string"},
                    "legal-hold": {"type": "string"},
                    "retention": {"type": "string"},
                },
                "required": ["bucketName", "key"],
                "type": "object",
            },
            "RetentionInfo": {
                "properties": {
                    "lastModifiedTime": {"format": "int64", "type": "integer"},
                    "retainUntilMode": {"type": "string"},
                    "retainUntilTime": {"format": "int64", "type": "integer"},
                },
                "type": "object",
            },
            "SessionContext": {
                "properties": {"attributes": {"$ref": "#/definitions/Attributes"}},
                "required": ["attributes"],
                "type": "object",
            },
            "UserIdentity": {
                "properties": {
                    "accessKeyId": {"type": "string"},
                    "accountId": {"type": "string"},
                    "arn": {"type": "string"},
                    "principalId": {"type": "string"},
                    "sessionContext": {"$ref": "#/definitions/SessionContext"},
                    "type": {"type": "string"},
                },
                "required": ["accessKeyId", "sessionContext", "accountId", "principalId", "type", "arn"],
                "type": "object",
            },
        },
        "properties": {
            "account": {"type": "string"},
            "detail": {"$ref": "#/definitions/AWSAPICallViaCloudTrail"},
            "detail-type": {"type": "string"},
            "id": {"type": "string"},
            "region": {"type": "string"},
            "resources": {"items": {"type": "string"}, "type": "array"},
            "source": {"type": "string"},
            "time": {"format": "date-time", "type": "string"},
            "version": {"type": "string"},
        },
        "required": ["detail-type", "resources", "id", "source", "time", "detail", "region", "version", "account"],
        "title": "AWSAPICallViaCloudTrail",
        "type": "object",
        "x-amazon-events-detail-type": "AWS API Call via CloudTrail",
        "x-amazon-events-source": "aws.s3",
    }
