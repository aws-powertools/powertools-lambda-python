---
title: Batch Processing
description: Utility
---

The batch processing utility handles partial failures when processing batches from Amazon SQS, Amazon Kinesis Data Streams, and Amazon DynamoDB Streams.

## Key Features

* Reports batch item failures to reduce number of retries for a record upon errors
* Simple interface to process each batch record
* Integrates with [Event Source Data Classes](./data_classes.md){target="_blank} and [Parser (Pydantic)](parser.md){target="_blank} for self-documenting record schema
* Build your own batch processor by extending primitives

## Background

When using SQS, Kinesis Data Streams, or DynamoDB Streams as a Lambda event source, your Lambda functions are triggered with a batch of messages.

If your function fails to process any message from the batch, the entire batch returns to your queue or stream. This same batch is then retried until either condition happens first: **a)** your Lambda function returns a successful response, **b)** record reaches maximum retry attempts, or **c)** when records expire.

With this utility, batch records are processed individually – only messages that failed to be processed return to the queue or stream for a further retry. This works when two mechanisms are in place:

1.  `ReportBatchItemFailures` is set in your SQS, Kinesis, or DynamoDB event source properties
2.  [A specific response](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html#sqs-batchfailurereporting-syntax){target="_blank"} is returned so Lambda knows which records should not be deleted during partial responses

!!! warning "This utility lowers the chance of processing records more than once; it does not guarantee it"
    We recommend implementing processing logic in an [idempotent manner](idempotency.md){target="_blank"} wherever possible.

    You can find more details on how Lambda works with either [SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html){target="_blank"}, [Kinesis](https://docs.aws.amazon.com/lambda/latest/dg/with-kinesis.html){target="_blank"}, or [DynamoDB](https://docs.aws.amazon.com/lambda/latest/dg/with-ddb.html){target="_blank"} in the AWS Documentation.

## Getting started

Regardless whether you're using SQS, Kinesis Data Streams or DynamoDB Streams, you must configure your Lambda function event source to use ``ReportBatchItemFailures`.

You do not need any additional IAM permissions to use this utility, except for what each event source requires.

### Required resources

The remaining sections of the documentation will rely on these samples. For completeness, this demonstrates IAM permissions and Dead Letter Queue where batch records will be sent after 2 retries were attempted.


=== "SQS"

    ```yaml title="template.yaml" hl_lines="31-32"
    AWSTemplateFormatVersion: '2010-09-09'
    Transform: AWS::Serverless-2016-10-31
    Description: partial batch response sample

    Globals:
        Function:
            Timeout: 5
            MemorySize: 256
            Runtime: python3.8
            Tracing: Active
            Environment:
                Variables:
                    LOG_LEVEL: INFO
                    POWERTOOLS_SERVICE_NAME: hello

    Resources:
        HelloWorldFunction:
            Type: AWS::Serverless::Function
            Properties:
                Handler: app.lambda_handler
                CodeUri: hello_world
                Policies:
                    - SQSPollerPolicy:
                        QueueName: !GetAtt SampleQueue.QueueName
                Events:
                    Batch:
                        Type: SQS
                        Properties:
                            Queue: !GetAtt SampleQueue.Arn
                            FunctionResponseTypes:
                                - ReportBatchItemFailures

        SampleDLQ:
            Type: AWS::SQS::Queue

        SampleQueue:
            Type: AWS::SQS::Queue
            Properties:
                VisibilityTimeout: 30 # Fn timeout * 6
                RedrivePolicy:
                    maxReceiveCount: 2
                    deadLetterTargetArn: !GetAtt SampleDLQ.Arn
    ```

=== "Kinesis Data Streams"

    ```yaml title="template.yaml" hl_lines="44-45"
    AWSTemplateFormatVersion: '2010-09-09'
    Transform: AWS::Serverless-2016-10-31
    Description: partial batch response sample

    Globals:
        Function:
            Timeout: 5
            MemorySize: 256
            Runtime: python3.8
            Tracing: Active
            Environment:
                Variables:
                    LOG_LEVEL: INFO
                    POWERTOOLS_SERVICE_NAME: hello

    Resources:
        HelloWorldFunction:
            Type: AWS::Serverless::Function
            Properties:
                Handler: app.lambda_handler
                CodeUri: hello_world
                Policies:
                    # Lambda Destinations require additional permissions
                    # to send failure records to DLQ from Kinesis/DynamoDB
                    - Version: "2012-10-17"
                      Statement:
                        Effect: "Allow"
                        Action:
                            - sqs:GetQueueAttributes
                            - sqs:GetQueueUrl
                            - sqs:SendMessage
                        Resource: !GetAtt SampleDLQ.Arn
                Events:
                    KinesisStream:
                        Type: Kinesis
                        Properties:
                            Stream: !GetAtt SampleStream.Arn
                            BatchSize: 100
                            StartingPosition: LATEST
                            MaximumRetryAttempts: 2
                            DestinationConfig:
                                OnFailure:
                                    Destination: !GetAtt SampleDLQ.Arn
                            FunctionResponseTypes:
                                - ReportBatchItemFailures

        SampleDLQ:
            Type: AWS::SQS::Queue

        SampleStream:
            Type: AWS::Kinesis::Stream
            Properties:
                ShardCount: 1
    ```

=== "DynamoDB Streams"

    ```yaml title="template.yaml" hl_lines="43-44"
    AWSTemplateFormatVersion: '2010-09-09'
    Transform: AWS::Serverless-2016-10-31
    Description: partial batch response sample

    Globals:
        Function:
            Timeout: 5
            MemorySize: 256
            Runtime: python3.8
            Tracing: Active
            Environment:
                Variables:
                    LOG_LEVEL: INFO
                    POWERTOOLS_SERVICE_NAME: hello

    Resources:
        HelloWorldFunction:
            Type: AWS::Serverless::Function
            Properties:
                Handler: app.lambda_handler
                CodeUri: hello_world
                Policies:
                    # Lambda Destinations require additional permissions
                    # to send failure records from Kinesis/DynamoDB
                    - Version: "2012-10-17"
                      Statement:
                        Effect: "Allow"
                        Action:
                            - sqs:GetQueueAttributes
                            - sqs:GetQueueUrl
                            - sqs:SendMessage
                        Resource: !GetAtt SampleDLQ.Arn
                Events:
                    DynamoDBStream:
                        Type: DynamoDB
                        Properties:
                            Stream: !GetAtt SampleTable.StreamArn
                            StartingPosition: LATEST
                            MaximumRetryAttempts: 2
                            DestinationConfig:
                                OnFailure:
                                    Destination: !GetAtt SampleDLQ.Arn
                            FunctionResponseTypes:
                                - ReportBatchItemFailures

        SampleDLQ:
            Type: AWS::SQS::Queue

        SampleTable:
            Type: AWS::DynamoDB::Table
            Properties:
                BillingMode: PAY_PER_REQUEST
                AttributeDefinitions:
                    - AttributeName: pk
                      AttributeType: S
                    - AttributeName: sk
                      AttributeType: S
                KeySchema:
                    - AttributeName: pk
                      KeyType: HASH
                    - AttributeName: sk
                      KeyType: RANGE
                SSESpecification:
                    SSEEnabled: yes
                StreamSpecification:
                    StreamViewType: NEW_AND_OLD_IMAGES

    ```

### Processing messages from SQS

Processing batches from SQS works in four stages:

1.  Instantiate **`BatchProcessor`** and choose **`EventType.SQS`** for the event type
2.  Define your function to handle each batch record, and use [`SQSRecord`](data_classes.md#sqs){target="_blank"} type annotation for autocompletion
3.  Use either **`batch_processor`** decorator or your instantiated processor as a context manager to kick off processing
4.  Return the appropriate response contract to Lambda via **`.response()`** processor method

!!! info "This code example optionally uses Tracer and Logger for completion"

=== "As a decorator"

    ```python hl_lines="4-5 9 15 23 25"
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
    from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = BatchProcessor(event_type=EventType.SQS)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: SQSRecord):
        payload: str = record.body
        if payload:
            item: dict = json.loads(payload)
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context: LambdaContext):
        return processor.response()
    ```

=== "As a context manager"

    ```python hl_lines="4-5 9 15 24-26 28"
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
    from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = BatchProcessor(event_type=EventType.SQS)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: SQSRecord):
        payload: str = record.body
        if payload:
            item: dict = json.loads(payload)
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    def lambda_handler(event, context: LambdaContext):
        batch = event["Records"]
        with processor(records=batch, processor=processor):
            processed_messages = processor.process() # kick off processing, return list[tuple]

        return processor.response()
    ```

=== "Sample response"

    The second record failed to be processed, therefore the processor added its message ID in the response.

    ```python
    {
        'batchItemFailures': [
            {
                'itemIdentifier': '244fc6b4-87a3-44ab-83d2-361172410c3a'
            }
        ]
    }
    ```

=== "Sample event"

    ```json
    {
        "Records": [
            {
                "messageId": "059f36b4-87a3-44ab-83d2-661975830a7d",
                "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a",
                "body": "{\"Message\": \"success\"}",
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1545082649183",
                    "SenderId": "AIDAIENQZJOLO23YVJ4VO",
                    "ApproximateFirstReceiveTimestamp": "1545082649185"
                },
                "messageAttributes": {},
                "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-2: 123456789012:my-queue",
                "awsRegion": "us-east-1"
            },
            {
                "messageId": "244fc6b4-87a3-44ab-83d2-361172410c3a",
                "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a",
                "body": "SGVsbG8sIHRoaXMgaXMgYSB0ZXN0Lg==",
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1545082649183",
                    "SenderId": "AIDAIENQZJOLO23YVJ4VO",
                    "ApproximateFirstReceiveTimestamp": "1545082649185"
                },
                "messageAttributes": {},
                "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-2: 123456789012:my-queue",
                "awsRegion": "us-east-1"
            }
        ]
    }
    ```

### Processing messages from Kinesis

Processing batches from Kinesis works in four stages:

1.  Instantiate **`BatchProcessor`** and choose **`EventType.KinesisDataStreams`** for the event type
2.  Define your function to handle each batch record, and use [`KinesisStreamRecord`](data_classes.md#kinesis-streams){target="_blank"} type annotation for autocompletion
3.  Use either **`batch_processor`** decorator or your instantiated processor as a context manager to kick off processing
4.  Return the appropriate response contract to Lambda via **`.response()`** processor method

!!! info "This code example optionally uses Tracer and Logger for completion"

=== "As a decorator"

    ```python hl_lines="4-5 9 15 22 24"
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
    from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import KinesisStreamRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = BatchProcessor(event_type=EventType.KinesisDataStreams)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: KinesisStreamRecord):
        logger.info(record.kinesis.data_as_text)
        payload: dict = record.kinesis.data_as_json()
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context: LambdaContext):
        return processor.response()
    ```

=== "As a context manager"

    ```python hl_lines="4-5 9 15 23-25 27"
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
    from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import KinesisStreamRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = BatchProcessor(event_type=EventType.KinesisDataStreams)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: KinesisStreamRecord):
        logger.info(record.kinesis.data_as_text)
        payload: dict = record.kinesis.data_as_json()
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    def lambda_handler(event, context: LambdaContext):
        batch = event["Records"]
        with processor(records=batch, processor=processor):
            processed_messages = processor.process() # kick off processing, return list[tuple]

        return processor.response()
    ```

=== "Sample response"

    The second record failed to be processed, therefore the processor added its sequence number in the response.

    ```python
    {
        'batchItemFailures': [
            {
                'itemIdentifier': '6006958808509702859251049540584488075644979031228738'
            }
        ]
    }
    ```


=== "Sample event"

    ```json
    {
        "Records": [
            {
                "kinesis": {
                    "kinesisSchemaVersion": "1.0",
                    "partitionKey": "1",
                    "sequenceNumber": "4107859083838847772757075850904226111829882106684065",
                    "data": "eyJNZXNzYWdlIjogInN1Y2Nlc3MifQ==",
                    "approximateArrivalTimestamp": 1545084650.987
                },
                "eventSource": "aws:kinesis",
                "eventVersion": "1.0",
                "eventID": "shardId-000000000006:4107859083838847772757075850904226111829882106684065",
                "eventName": "aws:kinesis:record",
                "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-role",
                "awsRegion": "us-east-2",
                "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream"
            },
            {
                "kinesis": {
                    "kinesisSchemaVersion": "1.0",
                    "partitionKey": "1",
                    "sequenceNumber": "6006958808509702859251049540584488075644979031228738",
                    "data": "c3VjY2Vzcw==",
                    "approximateArrivalTimestamp": 1545084650.987
                },
                "eventSource": "aws:kinesis",
                "eventVersion": "1.0",
                "eventID": "shardId-000000000006:6006958808509702859251049540584488075644979031228738",
                "eventName": "aws:kinesis:record",
                "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-role",
                "awsRegion": "us-east-2",
                "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream"
            }
        ]
    }
    ```


### Processing messages from DynamoDB

Processing batches from Kinesis works in four stages:

1.  Instantiate **`BatchProcessor`** and choose **`EventType.DynamoDBStreams`** for the event type
2.  Define your function to handle each batch record, and use [`DynamoDBRecord`](data_classes.md#dynamodb-streams){target="_blank"} type annotation for autocompletion
3.  Use either **`batch_processor`** decorator or your instantiated processor as a context manager to kick off processing
4.  Return the appropriate response contract to Lambda via **`.response()`** processor method

!!! info "This code example optionally uses Tracer and Logger for completion"

=== "As a decorator"

    ```python hl_lines="4-5 9 15 25 27"
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
    from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = BatchProcessor(event_type=EventType.DynamoDBStreams)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: DynamoDBRecord):
        logger.info(record.dynamodb.new_image)
        payload: dict = json.loads(record.dynamodb.new_image.get("Message").get_value)
        # alternatively:
        # changes: Dict[str, dynamo_db_stream_event.AttributeValue] = record.dynamodb.new_image
        # payload = change.get("Message").raw_event -> {"S": "<payload>"}
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context: LambdaContext):
        return processor.response()
    ```

=== "As a context manager"

    ```python hl_lines="4-5 9 15 26-28 30"
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
    from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = BatchProcessor(event_type=EventType.DynamoDBStreams)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: DynamoDBRecord):
        logger.info(record.dynamodb.new_image)
        payload: dict = json.loads(record.dynamodb.new_image.get("item").s_value)
        # alternatively:
        # changes: Dict[str, dynamo_db_stream_event.AttributeValue] = record.dynamodb.new_image
        # payload = change.get("Message").raw_event -> {"S": "<payload>"}
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    def lambda_handler(event, context: LambdaContext):
        batch = event["Records"]
        with processor(records=batch, processor=processor):
            processed_messages = processor.process() # kick off processing, return list[tuple]

        return processor.response()
    ```

=== "Sample response"

    The second record failed to be processed, therefore the processor added its sequence number in the response.

    ```python
    {
        'batchItemFailures': [
            {
                'itemIdentifier': '8640712661'
            }
        ]
    }
    ```


=== "Sample event"

    ```json
    {
        "Records": [
            {
                "eventID": "1",
                "eventVersion": "1.0",
                "dynamodb": {
                    "Keys": {
                        "Id": {
                            "N": "101"
                        }
                    },
                    "NewImage": {
                        "Message": {
                            "S": "failure"
                        }
                    },
                    "StreamViewType": "NEW_AND_OLD_IMAGES",
                    "SequenceNumber": "3275880929",
                    "SizeBytes": 26
                },
                "awsRegion": "us-west-2",
                "eventName": "INSERT",
                "eventSourceARN": "eventsource_arn",
                "eventSource": "aws:dynamodb"
            },
            {
                "eventID": "1",
                "eventVersion": "1.0",
                "dynamodb": {
                    "Keys": {
                        "Id": {
                            "N": "101"
                        }
                    },
                    "NewImage": {
                        "SomethingElse": {
                            "S": "success"
                        }
                    },
                    "StreamViewType": "NEW_AND_OLD_IMAGES",
                    "SequenceNumber": "8640712661",
                    "SizeBytes": 26
                },
                "awsRegion": "us-west-2",
                "eventName": "INSERT",
                "eventSourceARN": "eventsource_arn",
                "eventSource": "aws:dynamodb"
            }
        ]
    }
    ```

### Partial failure mechanics

All records in the batch will be passed to this handler for processing, even if exceptions are thrown - Here's the behaviour after completing the batch:

* **All records successfully processed**. We will return an empty list of item failures `{'batchItemFailures': []}`
* **Partial success with some exceptions**. We will return a list of all item IDs/sequence numbers that failed processing
* **All records failed to be processed**. We will raise `BatchProcessingError` exception with a list of all exceptions raised when processing

!!! warning
    You will not have access to the **processed messages** within the Lambda Handler; use context manager for that.

    All processing logic will and should be performed by the `record_handler` function.


<!-- ### IAM Permissions

Before your use this utility, your AWS Lambda function must have `sqs:DeleteMessageBatch` permission to delete successful messages directly from the queue.

> Example using AWS Serverless Application Model (SAM)

=== "template.yml"

    ```yaml hl_lines="2-3 12-15"
    Resources:
        MyQueue:
        Type: AWS::SQS::Queue

        HelloWorldFunction:
        Type: AWS::Serverless::Function
        Properties:
            Runtime: python3.8
            Environment:
            Variables:
                POWERTOOLS_SERVICE_NAME: example
            Policies:
            - SQSPollerPolicy:
                QueueName:
                    !GetAtt MyQueue.QueueName
    ```

### Processing messages from SQS

You can use either `sqs_batch_processor` decorator, or `PartialSQSProcessor` as a context manager if you'd like access to the processed results.

You need to create a function to handle each record from the batch - We call it `record_handler` from here on.

=== "Decorator"

    ```python hl_lines="3 6"
    from aws_lambda_powertools.utilities.batch import sqs_batch_processor

    def record_handler(record):
        return do_something_with(record["body"])

    @sqs_batch_processor(record_handler=record_handler)
    def lambda_handler(event, context):
        return {"statusCode": 200}
    ```
=== "Context manager"

    ```python hl_lines="3 9 11-12"
    from aws_lambda_powertools.utilities.batch import PartialSQSProcessor

    def record_handler(record):
        return_value = do_something_with(record["body"])
        return return_value

    def lambda_handler(event, context):
        records = event["Records"]
        processor = PartialSQSProcessor()

        with processor(records, record_handler) as proc:
            result = proc.process()  # Returns a list of all results from record_handler

        return result
    ```

!!! tip
    **Any non-exception/successful return from your record handler function** will instruct both decorator and context manager to queue up each individual message for deletion.

    If the entire batch succeeds, we let Lambda to proceed in deleting the records from the queue for cost reasons. -->


## Advanced

### Accessing processed messages

Use the context manager to access a list of all returned values from your `record_handler` function.

> Signature: List[Tuple[Union[SuccessResponse, FailureResponse]]]

* **When successful**. We will include a tuple with `success`, the result of `record_handler`, and the batch record
* **When failed**. We will include a tuple with `fail`, exception as a string, and the batch record


=== "app.py"

    ```python hl_lines="31-38"
    import json

    from typing import Any, List, Literal, Union

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import (BatchProcessor,
                                                       EventType,
                                                       FailureResponse,
                                                       SuccessResponse,
                                                       batch_processor)
    from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = BatchProcessor(event_type=EventType.SQS)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: SQSRecord):
        payload: str = record.body
        if payload:
            item: dict = json.loads(payload)
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    def lambda_handler(event, context: LambdaContext):
        batch = event["Records"]
        with processor(records=batch, processor=processor):
            processed_messages: List[Union[SuccessResponse, FailureResponse]] = processor.process()

        for messages in processed_messages:
            for message in messages:
                status: Union[Literal["success"], Literal["fail"]] = message[0]
                result: Any = message[1]
                record: SQSRecord = message[2]


        return processor.response()
    ```


### Extending BatchProcessor

You might want to bring custom logic to the existing `BatchProcessor` to slightly override how we handle successes and failures.

For these scenarios, you can subclass `BatchProcessor` and quickly override `success_handler` and `failure_handler` methods:

* **`success_handler()`** – Keeps track of successful batch records
* **`failure_handler()`** – Keeps track of failed batch records

**Example**

Let's suppose you'd like to add a metric named `BatchRecordFailures` for each batch record that failed processing:

=== "app.py"

    ```python

    from typing import Tuple

    from aws_lambda_powertools import Metrics
    from aws_lambda_powertools.metrics import MetricUnit
    from aws_lambda_powertools.utilities.batch import batch_processor, BatchProcessor, ExceptionInfo, EventType, FailureResponse
    from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord


    class MyProcessor(BatchProcessor):
        def failure_handler(self, record: SQSRecord, exception: ExceptionInfo) -> FailureResponse:
            metrics.add_metric(name="BatchRecordFailures", unit=MetricUnit.Count, value=1)
            return super().failure_handler(record, exception)

    processor = MyProcessor(event_type=EventType.SQS)
    metrics = Metrics(namespace="test")


    @tracer.capture_method
    def record_handler(record: SQSRecord):
        payload: str = record.body
        if payload:
            item: dict = json.loads(payload)
        ...

    @metrics.log_metrics(capture_cold_start_metric=True)
    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context: LambdaContext):
        return processor.response()
    ```

### Create your own partial processor

You can create your own partial batch processor from scratch by inheriting the `BasePartialProcessor` class, and implementing `_prepare()`, `_clean()` and `_process_record()`.

* **`_process_record()`** – handles all processing logic for each individual message of a batch, including calling the `record_handler` (self.handler)
* **`_prepare()`** – called once as part of the processor initialization
* **`clean()`** – teardown logic called once after `_process_record` completes

You can then use this class as a context manager, or pass it to `batch_processor` to use as a decorator on your Lambda handler function.

=== "custom_processor.py"

    ```python hl_lines="3 9 24 30 37 57"
    from random import randint

    from aws_lambda_powertools.utilities.batch import BasePartialProcessor, batch_processor
    import boto3
    import os

    table_name = os.getenv("TABLE_NAME", "table_not_found")

    class MyPartialProcessor(BasePartialProcessor):
        """
        Process a record and stores successful results at a Amazon DynamoDB Table

        Parameters
        ----------
        table_name: str
            DynamoDB table name to write results to
        """

        def __init__(self, table_name: str):
            self.table_name = table_name

            super().__init__()

        def _prepare(self):
            # It's called once, *before* processing
            # Creates table resource and clean previous results
            self.ddb_table = boto3.resource("dynamodb").Table(self.table_name)
            self.success_messages.clear()

        def _clean(self):
            # It's called once, *after* closing processing all records (closing the context manager)
            # Here we're sending, at once, all successful messages to a ddb table
            with ddb_table.batch_writer() as batch:
                for result in self.success_messages:
                    batch.put_item(Item=result)

        def _process_record(self, record):
            # It handles how your record is processed
            # Here we're keeping the status of each run
            # where self.handler is the record_handler function passed as an argument
            try:
                result = self.handler(record) # record_handler passed to decorator/context manager
                return self.success_handler(record, result)
            except Exception as exc:
                return self.failure_handler(record, exc)

        def success_handler(self, record):
            entry = ("success", result, record)
            message = {"age": result}
            self.success_messages.append(message)
            return entry


    def record_handler(record):
        return randint(0, 100)

    @batch_processor(record_handler=record_handler, processor=MyPartialProcessor(table_name))
    def lambda_handler(event, context):
        return {"statusCode": 200}
    ```


## FAQ

### Choosing between decorator and context manager

Use context manager when you want access to the processed messages or handle `BatchProcessingError` exception when all records within the batch fail to be processed.

### Integrating exception handling with Sentry.io

When using Sentry.io for error monitoring, you can override `failure_handler` to capture each processing exception with Sentry SDK:

> Credits to [Charles-Axel Dein](https://github.com/awslabs/aws-lambda-powertools-python/issues/293#issuecomment-781961732)

=== "sentry_integration.py"

    ```python hl_lines="4 7-8"
    from typing import Tuple

    from aws_lambda_powertools.utilities.batch import BatchProcessor, FailureResponse
    from sentry_sdk import capture_exception


    class MyProcessor(BatchProcessor):
        def failure_handler(self, record, exception) -> FailureResponse:
            capture_exception()  # send exception to Sentry
            return super().failure_handler(record, exception)
    ```


## Legacy

!!! tip "This is kept for historical purposes. Use the new [BatchProcessor](#processing-messages-from-sqs) instead. "

### Customizing boto configuration

The **`config`** and **`boto3_session`** parameters enable you to pass in a custom [botocore config object](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html)
or a custom [boto3 session](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html) when using the `sqs_batch_processor`
decorator or `PartialSQSProcessor` class.

> Custom config example

=== "Decorator"

    ```python  hl_lines="4 12"
    from aws_lambda_powertools.utilities.batch import sqs_batch_processor
    from botocore.config import Config

    config = Config(region_name="us-east-1")

    def record_handler(record):
        # This will be called for each individual message from a batch
        # It should raise an exception if the message was not processed successfully
        return_value = do_something_with(record["body"])
        return return_value

    @sqs_batch_processor(record_handler=record_handler, config=config)
    def lambda_handler(event, context):
        return {"statusCode": 200}
    ```

=== "Context manager"

    ```python  hl_lines="4 16"
    from aws_lambda_powertools.utilities.batch import PartialSQSProcessor
    from botocore.config import Config

    config = Config(region_name="us-east-1")

    def record_handler(record):
        # This will be called for each individual message from a batch
        # It should raise an exception if the message was not processed successfully
        return_value = do_something_with(record["body"])
        return return_value


    def lambda_handler(event, context):
        records = event["Records"]

        processor = PartialSQSProcessor(config=config)

        with processor(records, record_handler):
            result = processor.process()

        return result
    ```

> Custom boto3 session example

=== "Decorator"

    ```python  hl_lines="4 12"
    from aws_lambda_powertools.utilities.batch import sqs_batch_processor
    from botocore.config import Config

    session = boto3.session.Session()

    def record_handler(record):
        # This will be called for each individual message from a batch
        # It should raise an exception if the message was not processed successfully
        return_value = do_something_with(record["body"])
        return return_value

    @sqs_batch_processor(record_handler=record_handler, boto3_session=session)
    def lambda_handler(event, context):
        return {"statusCode": 200}
    ```

=== "Context manager"

    ```python  hl_lines="4 16"
    from aws_lambda_powertools.utilities.batch import PartialSQSProcessor
    import boto3

    session = boto3.session.Session()

    def record_handler(record):
        # This will be called for each individual message from a batch
        # It should raise an exception if the message was not processed successfully
        return_value = do_something_with(record["body"])
        return return_value


    def lambda_handler(event, context):
        records = event["Records"]

        processor = PartialSQSProcessor(boto3_session=session)

        with processor(records, record_handler):
            result = processor.process()

        return result
    ```

### Suppressing exceptions

If you want to disable the default behavior where `SQSBatchProcessingError` is raised if there are any errors, you can pass the `suppress_exception` boolean argument.

=== "Decorator"

    ```python hl_lines="3"
    from aws_lambda_powertools.utilities.batch import sqs_batch_processor

    @sqs_batch_processor(record_handler=record_handler, config=config, suppress_exception=True)
    def lambda_handler(event, context):
        return {"statusCode": 200}
    ```

=== "Context manager"

    ```python hl_lines="3"
    from aws_lambda_powertools.utilities.batch import PartialSQSProcessor

    processor = PartialSQSProcessor(config=config, suppress_exception=True)

    with processor(records, record_handler):
        result = processor.process()
    ```
