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

???+ warning "Warning: This utility lowers the chance of processing records more than once; it does not guarantee it"
    We recommend implementing processing logic in an [idempotent manner](idempotency.md){target="_blank"} wherever possible.

    You can find more details on how Lambda works with either [SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html){target="_blank"}, [Kinesis](https://docs.aws.amazon.com/lambda/latest/dg/with-kinesis.html){target="_blank"}, or [DynamoDB](https://docs.aws.amazon.com/lambda/latest/dg/with-ddb.html){target="_blank"} in the AWS Documentation.

## Getting started

Regardless whether you're using SQS, Kinesis Data Streams or DynamoDB Streams, you must configure your Lambda function event source to use ``ReportBatchItemFailures`.

You do not need any additional IAM permissions to use this utility, except for what each event source requires.

### Required resources

The remaining sections of the documentation will rely on these samples. For completeness, this demonstrates IAM permissions and Dead Letter Queue where batch records will be sent after 2 retries were attempted.

=== "SQS"

    ```yaml title="template.yaml" hl_lines="30-31"
    --8<-- "docs/examples/utilities/batch/sqs_template.yml"
    ```

=== "Kinesis Data Streams"

    ```yaml title="template.yaml" hl_lines="44-45"
    --8<-- "docs/examples/utilities/batch/kinesis_data_streams_template.yml"
    ```

=== "DynamoDB Streams"

    ```yaml title="template.yaml" hl_lines="43-44"
    --8<-- "docs/examples/utilities/batch/dynamodb_streams_template.yml"
    ```

### Processing messages from SQS

Processing batches from SQS works in four stages:

1. Instantiate **`BatchProcessor`** and choose **`EventType.SQS`** for the event type
2. Define your function to handle each batch record, and use [`SQSRecord`](data_classes.md#sqs){target="_blank"} type annotation for autocompletion
3. Use either **`batch_processor`** decorator or your instantiated processor as a context manager to kick off processing
4. Return the appropriate response contract to Lambda via **`.response()`** processor method

???+ info
    This code example optionally uses Tracer and Logger for completion.

=== "As a decorator"

    ```python hl_lines="4-5 8 14 23 25"
    --8<-- "docs/examples/utilities/batch/sqs_decorator.py"
    ```

=== "As a context manager"

    ```python hl_lines="4-5 8 14 24-26 28"
    --8<-- "docs/examples/utilities/batch/sqs_context_manager.py"
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

1. Instantiate **`BatchProcessor`** and choose **`EventType.KinesisDataStreams`** for the event type
2. Define your function to handle each batch record, and use [`KinesisStreamRecord`](data_classes.md#kinesis-streams){target="_blank"} type annotation for autocompletion
3. Use either **`batch_processor`** decorator or your instantiated processor as a context manager to kick off processing
4. Return the appropriate response contract to Lambda via **`.response()`** processor method

???+ info
    This code example optionally uses Tracer and Logger for completion.

=== "As a decorator"

    ```python hl_lines="4-5 8 14 22 24"
    --8<-- "docs/examples/utilities/batch/kinesis_data_streams_decorator.py"
    ```

=== "As a context manager"

    ```python hl_lines="4-5 8 14 23-25 27"
    --8<-- "docs/examples/utilities/batch/kinesis_data_streams_context_manager.py"
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

1. Instantiate **`BatchProcessor`** and choose **`EventType.DynamoDBStreams`** for the event type
2. Define your function to handle each batch record, and use [`DynamoDBRecord`](data_classes.md#dynamodb-streams){target="_blank"} type annotation for autocompletion
3. Use either **`batch_processor`** decorator or your instantiated processor as a context manager to kick off processing
4. Return the appropriate response contract to Lambda via **`.response()`** processor method

???+ info
    This code example optionally uses Tracer and Logger for completion.

=== "As a decorator"

    ```python hl_lines="4-5 8 14 25 27"
    --8<-- "docs/examples/utilities/batch/dynamodb_streams_decorator.py"
    ```

=== "As a context manager"

    ```python hl_lines="4-5 8 14 26-28 30"
    --8<-- "docs/examples/utilities/batch/dynamodb_streams_context_manager.py"
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

???+ warning
    You will not have access to the **processed messages** within the Lambda Handler; use context manager for that.

    All processing logic will and should be performed by the `record_handler` function.

## Advanced

### Pydantic integration

You can bring your own Pydantic models via **`model`** parameter when inheriting from **`SqsRecordModel`**, **`KinesisDataStreamRecord`**, or **`DynamoDBStreamRecordModel`**

Inheritance is importance because we need to access message IDs and sequence numbers from these records in the event of failure. Mypy is fully integrated with this utility, so it should identify whether you're passing the incorrect Model.

=== "SQS"

    ```python hl_lines="6 10-11 14-21 24 30"
    --8<-- "docs/examples/utilities/batch/sqs_pydantic_inheritance.py"
    ```

=== "Kinesis Data Streams"

    ```python hl_lines="8 12-13 16-24 27-28 31 37"
    --8<-- "docs/examples/utilities/batch/kinesis_data_streams_pydantic_inheritance.py"
    ```

=== "DynamoDB Streams"

    ```python hl_lines="7 11-12 15-22 25-27 30-31 34 40"
    --8<-- "docs/examples/utilities/batch/dynamodb_streams_pydantic_inheritance.py"
    ```

### Accessing processed messages

Use the context manager to access a list of all returned values from your `record_handler` function.

* **When successful**. We will include a tuple with `success`, the result of `record_handler`, and the batch record
* **When failed**. We will include a tuple with `fail`, exception as a string, and the batch record

```python hl_lines="5 26-27 29-32" title="Accessing processed messages via context manager"
--8<-- "docs/examples/utilities/batch/sqs_processed_messages_context_manager.py"
```

### Extending BatchProcessor

You might want to bring custom logic to the existing `BatchProcessor` to slightly override how we handle successes and failures.

For these scenarios, you can subclass `BatchProcessor` and quickly override `success_handler` and `failure_handler` methods:

* **`success_handler()`** – Keeps track of successful batch records
* **`failure_handler()`** – Keeps track of failed batch records

???+ example
	Let's suppose you'd like to add a metric named `BatchRecordFailures` for each batch record that failed processing

```python title="Extending failure handling mechanism in BatchProcessor"
--8<-- "docs/examples/utilities/batch/sqs_batch_processor_extension.py"
```

### Create your own partial processor

You can create your own partial batch processor from scratch by inheriting the `BasePartialProcessor` class, and implementing `_prepare()`, `_clean()` and `_process_record()`.

* **`_process_record()`** – handles all processing logic for each individual message of a batch, including calling the `record_handler` (self.handler)
* **`_prepare()`** – called once as part of the processor initialization
* **`clean()`** – teardown logic called once after `_process_record` completes

You can then use this class as a context manager, or pass it to `batch_processor` to use as a decorator on your Lambda handler function.

```python hl_lines="6 11 26 32 39 60" title="Creating a custom batch processor"
--8<-- "docs/examples/utilities/batch/custom_batch_processor.py"
```

### Caveats

#### Tracer response auto-capture for large batch sizes

When using Tracer to capture responses for each batch record processing, you might exceed 64K of tracing data depending on what you return from your `record_handler` function, or how big is your batch size.

If that's the case, you can configure [Tracer to disable response auto-capturing](../core/tracer.md#disabling-response-auto-capture){target="_blank"}.

```python hl_lines="13" title="Disabling Tracer response auto-capturing"
--8<-- "docs/examples/utilities/batch/caveats_tracer_response_auto_capture.py"
```

## Testing your code

As there is no external calls, you can unit test your code with `BatchProcessor` quite easily.

**Example**:

Given a SQS batch where the first batch record succeeds and the second fails processing, we should have a single item reported in the function response.

=== "test_app.py"

    ```python
    --8<-- "docs/examples/utilities/batch/testing_test_app.py"
    ```

=== "src/app.py"

    ```python
    --8<-- "docs/examples/utilities/batch/testing_src_app.py"
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

### Integrating exception handling with Sentry.io

When using Sentry.io for error monitoring, you can override `failure_handler` to capture each processing exception with Sentry SDK:

> Credits to [Charles-Axel Dein](https://github.com/awslabs/aws-lambda-powertools-python/issues/293#issuecomment-781961732)

```python hl_lines="3 8-9" title="Integrating error tracking with Sentry.io"
--8<-- "docs/examples/utilities/batch/sentry_integration.py"
```

## Legacy

???+ tip
    This is kept for historical purposes. Use the new [BatchProcessor](#processing-messages-from-sqs) instead.

### Migration guide

???+ info
    Keep reading if you are using `sqs_batch_processor` or `PartialSQSProcessor`.

[As of Nov 2021](https://aws.amazon.com/about-aws/whats-new/2021/11/aws-lambda-partial-batch-response-sqs-event-source/){target="_blank"}, this is no longer needed as both SQS, Kinesis, and DynamoDB Streams offer this capability natively with one caveat - it's an [opt-in feature](#required-resources).

Being a native feature, we no longer need to instantiate boto3 nor other customizations like exception suppressing – this lowers the cost of your Lambda function as you can delegate deleting partial failures to Lambda.

???+ tip
    It's also easier to test since it's mostly a [contract based response](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html#sqs-batchfailurereporting-syntax){target="_blank"}.

You can migrate in three steps:

1. If you are using **`sqs_batch_decorator`** you can now use **`batch_processor`** decorator
2. If you were using **`PartialSQSProcessor`** you can now use **`BatchProcessor`**
3. Change your Lambda Handler to return the new response format

=== "Decorator: Before"

    ```python hl_lines="1 8"
    --8<-- "docs/examples/utilities/batch/migration_decorator_before.py"
    ```

=== "Decorator: After"

    ```python hl_lines="3 5 12"
    --8<-- "docs/examples/utilities/batch/migration_decorator_after.py"
    ```

=== "Context manager: Before"

    ```python hl_lines="1 3 5 16 21"
    --8<-- "docs/examples/utilities/batch/migration_context_manager_before.py"
    ```

=== "Context manager: After"

    ```python hl_lines="1 12"
    --8<-- "docs/examples/utilities/batch/migration_context_manager_after.py"
    ```

### Customizing boto configuration

The **`config`** and **`boto3_session`** parameters enable you to pass in a custom [botocore config object](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html)
or a custom [boto3 session](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html) when using the `sqs_batch_processor`
decorator or `PartialSQSProcessor` class.

> Custom config example

=== "Decorator"

    ```python  hl_lines="5 15"
    --8<-- "docs/examples/utilities/batch/custom_config_decorator.py"
    ```

=== "Context manager"

    ```python  hl_lines="5 18"
    --8<-- "docs/examples/utilities/batch/custom_config_context_manager.py"
    ```

> Custom boto3 session example

=== "Decorator"

    ```python  hl_lines="5 15"
    --8<-- "docs/examples/utilities/batch/custom_boto3_session_decorator.py"
    ```

=== "Context manager"

    ```python  hl_lines="5 18"
    --8<-- "docs/examples/utilities/batch/custom_boto3_session_context_manager.py"
    ```

### Suppressing exceptions

If you want to disable the default behavior where `SQSBatchProcessingError` is raised if there are any errors, you can pass the `suppress_exception` boolean argument.

=== "Decorator"

    ```python hl_lines="6"
    --8<-- "docs/examples/utilities/batch/suppress_exception_decorator_sqs_batch_processor.py"
    ```

=== "Context manager"

    ```python hl_lines="5"
    --8<-- "docs/examples/utilities/batch/suppress_exception_partial_sqs_processor.py"
    ```
