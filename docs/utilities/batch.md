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

1. `ReportBatchItemFailures` is set in your SQS, Kinesis, or DynamoDB event source properties
2. [A specific response](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html#sqs-batchfailurereporting-syntax){target="_blank"} is returned so Lambda knows which records should not be deleted during partial responses

<!-- HTML tags are required in admonition content thus increasing line length beyond our limits -->
<!-- markdownlint-disable MD013 -->
???+ warning "Warning: This utility lowers the chance of processing records more than once; it does not guarantee it"
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
            Runtime: python3.9
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
            Runtime: python3.9
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
            Runtime: python3.9
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

Processing batches from SQS works in three stages:

1. Instantiate **`BatchProcessor`** and choose **`EventType.SQS`** for the event type
2. Define your function to handle each batch record, and use [`SQSRecord`](data_classes.md#sqs){target="_blank"} type annotation for autocompletion
3. Use **`process_partial_response`** to kick off processing

???+ info
    This code example optionally uses Tracer and Logger for completion.

=== "Recommended"

    ```python hl_lines="4 9 12 18 29"
    --8<-- "examples/batch_processing/src/getting_started_sqs.py"
    ```

=== "As a context manager"

    ```python hl_lines="4-5 9 15 24-26 28"
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType
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
        with processor(records=batch, handler=record_handler):
            processed_messages = processor.process() # kick off processing, return list[tuple]

        return processor.response()
    ```

=== "As a decorator (legacy)"

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

#### FIFO queues

When using [SQS FIFO queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues.html){target="_blank"}, we will stop processing messages after the first failure, and return all failed and unprocessed messages in `batchItemFailures`.
This helps preserve the ordering of messages in your queue.

=== "Recommended"

    ```python hl_lines="3 9"
    --8<-- "examples/batch_processing/src/getting_started_sqs_fifo.py"
    ```

=== "As a context manager"

    ```python hl_lines="2 6"
    --8<-- "examples/batch_processing/src/getting_started_sqs_fifo_context_manager.py"
    ```

=== "As a decorator (legacy)"

    ```python hl_lines="3 9"
    --8<-- "examples/batch_processing/src/getting_started_sqs_fifo_decorator.py"
    ```

### Processing messages from Kinesis

Processing batches from Kinesis works in three stages:

1. Instantiate **`BatchProcessor`** and choose **`EventType.KinesisDataStreams`** for the event type
2. Define your function to handle each batch record, and use [`KinesisStreamRecord`](data_classes.md#kinesis-streams){target="_blank"} type annotation for autocompletion
3. Use **`process_partial_response`** to kick off processing

???+ info
    This code example optionally uses Tracer and Logger for completion.

=== "Recommended"

    ```python hl_lines="2 7 12 18 28"
    --8<-- "examples/batch_processing/src/getting_started_kinesis.py"
    ```

=== "As a context manager"

    ```python hl_lines="4-5 9 15 23-25 27"
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType
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
        with processor(records=batch, handler=record_handler):
            processed_messages = processor.process() # kick off processing, return list[tuple]

        return processor.response()
    ```

=== "As a decorator (legacy)"

    ```python hl_lines="2-3 7 20 22"
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

Processing batches from Kinesis works in three stages:

1. Instantiate **`BatchProcessor`** and choose **`EventType.DynamoDBStreams`** for the event type
2. Define your function to handle each batch record, and use [`DynamoDBRecord`](data_classes.md#dynamodb-streams){target="_blank"} type annotation for autocompletion
3. Use **`process_partial_response`** to kick off processing

???+ info
    This code example optionally uses Tracer and Logger for completion.

=== "Recommended"

    ```python hl_lines="4 9 14 20 30"
    --8<-- "examples/batch_processing/src/getting_started_dynamodb.py"
    ```

=== "As a context manager"

    ```python hl_lines="4-5 9 15 23-27"
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType
    from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext


    processor = BatchProcessor(event_type=EventType.DynamoDBStreams)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: DynamoDBRecord):
        logger.info(record.dynamodb.new_image)
        payload: dict = json.loads(record.dynamodb.new_image.get("Message"))
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    def lambda_handler(event, context: LambdaContext):
        batch = event["Records"]
        with processor(records=batch, handler=record_handler):
            processed_messages = processor.process() # kick off processing, return list[tuple]

        return processor.response()
    ```

=== "As a decorator (legacy)"

    ```python hl_lines="4-5 9 15 22 24"
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
        payload: dict = json.loads(record.dynamodb.new_image.get("Message"))
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context: LambdaContext):
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

### Processing messages asynchronously

!!! tip "New to AsyncIO? Read this [comprehensive guide first](https://realpython.com/async-io-python/){target="_blank"}."

You can use `AsyncBatchProcessor` class and `async_process_partial_response` function to process messages concurrently.

???+ question "When is this useful?"
    Your use case might be able to process multiple records at the same time without conflicting with one another.

    For example, imagine you need to process multiple loyalty points and incrementally save in a database. While you await the database to confirm your records are saved, you could start processing another request concurrently.

    The reason this is not the default behaviour is that not all use cases can handle concurrency safely (e.g., loyalty points must be updated in order).

```python hl_lines="3 11 14 24" title="High-concurrency with AsyncBatchProcessor"
--8<-- "examples/batch_processing/src/getting_started_async.py"
```

???+ warning "Using tracer?"
    `AsyncBatchProcessor` uses `asyncio.gather` which can cause side effects and reach trace limits at high concurrency.

    See [Tracing concurrent asynchronous functions](../core/tracer.md#concurrent-asynchronous-functions).

## Advanced

### Pydantic integration

You can bring your own Pydantic models via **`model`** parameter when inheriting from **`SqsRecordModel`**, **`KinesisDataStreamRecord`**, or **`DynamoDBStreamRecordModel`**

Inheritance is importance because we need to access message IDs and sequence numbers from these records in the event of failure. Mypy is fully integrated with this utility, so it should identify whether you're passing the incorrect Model.

=== "SQS"

    ```python hl_lines="5 14 23 29"
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, process_partial_response
    from aws_lambda_powertools.utilities.parser.models import SqsRecordModel
    from aws_lambda_powertools.utilities.typing import LambdaContext
    from aws_lambda_powertools.utilities.parser import BaseModel
    from aws_lambda_powertools.utilities.parser.types import Json


    class Order(BaseModel):
        item: dict

    class OrderSqsRecord(SqsRecordModel):
        body: Json[Order]  # deserialize order data from JSON string

    processor = BatchProcessor(event_type=EventType.SQS, model=OrderSqsRecord)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: OrderSqsRecord):
        return record.body.item

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    def lambda_handler(event, context: LambdaContext):
        return process_partial_response(event=event, record_handler=record_handler, processor=processor, context=context)
    ```

=== "Kinesis Data Streams"

    ```python hl_lines="5 15 19 23 29 36"
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, process_partial_response
    from aws_lambda_powertools.utilities.parser.models import KinesisDataStreamRecordPayload, KinesisDataStreamRecord
    from aws_lambda_powertools.utilities.parser import BaseModel, validator
    from aws_lambda_powertools.utilities.parser.types import Json
    from aws_lambda_powertools.utilities.typing import LambdaContext


    class Order(BaseModel):
        item: dict


    class OrderKinesisPayloadRecord(KinesisDataStreamRecordPayload):
        data: Json[Order]


    class OrderKinesisRecord(KinesisDataStreamRecord):
        kinesis: OrderKinesisPayloadRecord


    processor = BatchProcessor(event_type=EventType.KinesisDataStreams, model=OrderKinesisRecord)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: OrderKinesisRecord):
        return record.kinesis.data.item


    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    def lambda_handler(event, context: LambdaContext):
        return process_partial_response(event=event, record_handler=record_handler, processor=processor, context=context)
    ```

=== "DynamoDB Streams"

    ```python hl_lines="7 16 26 31 35 41"
    import json

    from typing import Dict, Literal, Optional

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, process_partial_response
    from aws_lambda_powertools.utilities.parser.models import DynamoDBStreamChangedRecordModel, DynamoDBStreamRecordModel
    from aws_lambda_powertools.utilities.typing import LambdaContext
    from aws_lambda_powertools.utilities.parser import BaseModel, validator


    class Order(BaseModel):
        item: dict


    class OrderDynamoDB(BaseModel):
        Message: Order

        # auto transform json string
        # so Pydantic can auto-initialize nested Order model
        @validator("Message", pre=True)
        def transform_message_to_dict(cls, value: Dict[Literal["S"], str]):
            return json.loads(value["S"])


    class OrderDynamoDBChangeRecord(DynamoDBStreamChangedRecordModel):
        NewImage: Optional[OrderDynamoDB]
        OldImage: Optional[OrderDynamoDB]


    class OrderDynamoDBRecord(DynamoDBStreamRecordModel):
        dynamodb: OrderDynamoDBChangeRecord


    processor = BatchProcessor(event_type=EventType.DynamoDBStreams, model=OrderDynamoDBRecord)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: OrderDynamoDBRecord):
        return record.dynamodb.NewImage.Message.item


    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    def lambda_handler(event, context: LambdaContext):
        return process_partial_response(event=event, record_handler=record_handler, processor=processor, context=context)
    ```

### Accessing processed messages

Use the context manager to access a list of all returned values from your `record_handler` function.

* **When successful**. We will include a tuple with `success`, the result of `record_handler`, and the batch record
* **When failed**. We will include a tuple with `fail`, exception as a string, and the batch record

```python hl_lines="30-36" title="Accessing processed messages via context manager"
import json

from typing import Any, List, Literal, Union

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import (BatchProcessor,
												   EventType,
												   FailureResponse,
												   SuccessResponse)
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
	with processor(records=batch, handler=record_handler):
		processed_messages: List[Union[SuccessResponse, FailureResponse]] = processor.process()

	for message in processed_messages:
        status: Union[Literal["success"], Literal["fail"]] = message[0]
        result: Any = message[1]
        record: SQSRecord = message[2]


	return processor.response()
```

### Accessing Lambda Context

Within your `record_handler` function, you might need access to the Lambda context to determine how much time you have left before your function times out.

We can automatically inject the [Lambda context](https://docs.aws.amazon.com/lambda/latest/dg/python-context.html){target="_blank"} into your `record_handler` if your function signature has a parameter named `lambda_context`. When using a context manager, you also need to pass the Lambda context object like in the example below.

=== "Recommended"

    ```python hl_lines="19"
    --8<-- "examples/batch_processing/src/advanced_accessing_lambda_context.py"
    ```

=== "As a decorator (legacy)"

    ```python hl_lines="15"
    from typing import Optional

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import (BatchProcessor, EventType,
                                                       batch_processor)
    from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext

    processor = BatchProcessor(event_type=EventType.SQS)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: SQSRecord, lambda_context: Optional[LambdaContext] = None):
        if lambda_context is not None:
            remaining_time = lambda_context.get_remaining_time_in_millis()
        ...


    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context: LambdaContext):
        return processor.response()
    ```

=== "As a context manager"

    ```python hl_lines="14 23"
    from typing import Optional

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType
    from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
    from aws_lambda_powertools.utilities.typing import LambdaContext

    processor = BatchProcessor(event_type=EventType.SQS)
    tracer = Tracer()
    logger = Logger()


    @tracer.capture_method
    def record_handler(record: SQSRecord, lambda_context: Optional[LambdaContext] = None):
        if lambda_context is not None:
            remaining_time = lambda_context.get_remaining_time_in_millis()
        ...

    @logger.inject_lambda_context
    @tracer.capture_lambda_handler
    def lambda_handler(event, context: LambdaContext):
        batch = event["Records"]
        with processor(records=batch, handler=record_handler, lambda_context=context):
            result = processor.process()

        return result
    ```

### Extending BatchProcessor

You might want to bring custom logic to the existing `BatchProcessor` to slightly override how we handle successes and failures.

For these scenarios, you can subclass `BatchProcessor` and quickly override `success_handler` and `failure_handler` methods:

* **`success_handler()`** – Keeps track of successful batch records
* **`failure_handler()`** – Keeps track of failed batch records

???+ example
	Let's suppose you'd like to add a metric named `BatchRecordFailures` for each batch record that failed processing

```python title="Extending failure handling mechanism in BatchProcessor"

from typing import Tuple

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.batch import BatchProcessor, ExceptionInfo, EventType, FailureResponse, process_partial_response
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
def lambda_handler(event, context: LambdaContext):
    return process_partial_response(event=event, record_handler=record_handler, processor=processor, context=context)
```

### Create your own partial processor

You can create your own partial batch processor from scratch by inheriting the `BasePartialProcessor` class, and implementing `_prepare()`, `_clean()` and `_process_record()`.

* **`_process_record()`** – handles all processing logic for each individual message of a batch, including calling the `record_handler` (self.handler)
* **`_prepare()`** – called once as part of the processor initialization
* **`clean()`** – teardown logic called once after `_process_record` completes

You can then use this class as a context manager, or pass it to `batch_processor` to use as a decorator on your Lambda handler function.

```python hl_lines="3 9 24 30 37 57" title="Creating a custom batch processor"
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
		with self.ddb_table.batch_writer() as batch:
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

### Caveats

#### Tracer response auto-capture for large batch sizes

When using Tracer to capture responses for each batch record processing, you might exceed 64K of tracing data depending on what you return from your `record_handler` function, or how big is your batch size.

If that's the case, you can configure [Tracer to disable response auto-capturing](../core/tracer.md#disabling-response-auto-capture){target="_blank"}.

```python hl_lines="14" title="Disabling Tracer response auto-capturing"
import json

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext


processor = BatchProcessor(event_type=EventType.SQS)
tracer = Tracer()
logger = Logger()


@tracer.capture_method(capture_response=False)
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

## Testing your code

As there is no external calls, you can unit test your code with `BatchProcessor` quite easily.

**Example**:

Given a SQS batch where the first batch record succeeds and the second fails processing, we should have a single item reported in the function response.

=== "test_app.py"

    ```python
    import json

    from pathlib import Path
    from dataclasses import dataclass

    import pytest
    from src.app import lambda_handler, processor


    def load_event(path: Path):
        with path.open() as f:
            return json.load(f)


    @pytest.fixture
    def lambda_context():
        @dataclass
        class LambdaContext:
            function_name: str = "test"
            memory_limit_in_mb: int = 128
            invoked_function_arn: str = "arn:aws:lambda:eu-west-1:809313241:function:test"
            aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

        return LambdaContext()

    @pytest.fixture()
    def sqs_event():
        """Generates API GW Event"""
        return load_event(path=Path("events/sqs_event.json"))


    def test_app_batch_partial_response(sqs_event, lambda_context):
        # GIVEN
        processor = app.processor  # access processor for additional assertions
        successful_record = sqs_event["Records"][0]
        failed_record = sqs_event["Records"][1]
        expected_response = {
            "batchItemFailures: [
                {
                    "itemIdentifier": failed_record["messageId"]
                }
            ]
        }

        # WHEN
        ret = app.lambda_handler(sqs_event, lambda_context)

        # THEN
        assert ret == expected_response
        assert len(processor.fail_messages) == 1
        assert processor.success_messages[0] == successful_record
    ```

=== "src/app.py"

    ```python
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, process_partial_response
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
        return process_partial_response(event=event, record_handler=record_handler, processor=processor, context=context)
    ```

=== "Sample SQS event"

    ```json title="events/sqs_sample.json"
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

## FAQ

### Choosing between decorator and context manager

Use context manager when you want access to the processed messages or handle `BatchProcessingError` exception when all records within the batch fail to be processed.

### What's the difference between the decorator and process_partial_response functions?

`batch_processor` and `async_batch_processor` decorators are now considered legacy. Historically, they were kept due to backwards compatibility and to minimize code changes between V1 and V2.

As 2.12.0, `process_partial_response` and `async_process_partial_response` are the recommended instead. It reduces boilerplate, smaller memory/CPU cycles, and it makes it less error prone - e.g., decorators required an additional return.

### Integrating exception handling with Sentry.io

When using Sentry.io for error monitoring, you can override `failure_handler` to capture each processing exception with Sentry SDK:

> Credits to [Charles-Axel Dein](https://github.com/awslabs/aws-lambda-powertools-python/issues/293#issuecomment-781961732)

```python hl_lines="4 7-8" title="Integrating error tracking with Sentry.io"
from typing import Tuple

from aws_lambda_powertools.utilities.batch import BatchProcessor, FailureResponse
from sentry_sdk import capture_exception


class MyProcessor(BatchProcessor):
	def failure_handler(self, record, exception) -> FailureResponse:
		capture_exception()  # send exception to Sentry
		return super().failure_handler(record, exception)
```
