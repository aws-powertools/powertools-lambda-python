---
title: Upgrade guide
description: Guide to update between major Powertools versions
---

<!-- markdownlint-disable MD043 -->

## Migrate to v2 from v1

We've made minimal breaking changes to make your transition to v2 as smooth as possible.

### Quick summary

| Area                               | Change                                                                                                                                                     | Code change required | IAM Permissions change required |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- | ------------------------------- |
| **Batch**                          | Removed legacy [SQS batch processor](#legacy-sqs-batch-processor) in favour of **`BatchProcessor`**.                                                       | Yes                  | -                               |
| **Environment variables**          | Removed legacy **`POWERTOOLS_EVENT_HANDLER_DEBUG`** in favour of [`POWERTOOLS_DEV`](index.md#optimizing-for-non-production-environments){target="_blank"}. | -                    | -                               |
| **Event Handler**                  | Added multi value headers and cookies support to [Response method](#event-handler-response-headers-and-cookies).                                           | Unit tests only      | -                               |
| **Event Source Data Classes**      | Replaced [DynamoDBStreamEvent](#dynamodbstreamevent-in-event-source-data-classes) `AttributeValue` with native Python types.                               | Yes                  | -                               |
| **Feature Flags** / **Parameters** | Updated [AppConfig API calls](#feature-flags-and-appconfig-parameter-utility) due to **`GetConfiguration`** API deprecation.                               | -                    | Yes                             |
| **Idempotency**                    | Updated [partition key](#idempotency-key-format) to include fully qualified function/method names.                                                         | -                    | -                               |

### Initial Steps

Before you start, we suggest making a copy of your current working project or create a new branch with git.

1. **Upgrade** Python to at least v3.7

2. **Ensure** you have the latest `aws-lambda-powertools`

    ```bash
    pip install aws-lambda-powertools -U
    ```

3. **Review** the following sections to confirm whether they affect your code

## Legacy SQS Batch Processor

The deprecated `PartialSQSProcessor` and `sqs_batch_processor` were removed.
You can migrate to the [native batch processing](https://aws.amazon.com/about-aws/whats-new/2021/11/aws-lambda-partial-batch-response-sqs-event-source/) capability by:

1. If you use **`sqs_batch_decorator`** you can now use **`batch_processor`** decorator
2. If you use **`PartialSQSProcessor`** you can now use **`BatchProcessor`**
3. [Enable the functionality](../utilities/batch#required-resources) on SQS
4. Change your Lambda Handler to return the new response format

=== "Decorator: Before"

     ```python hl_lines="1 6"
     from aws_lambda_powertools.utilities.batch import sqs_batch_processor

     def record_handler(record):
         return do_something_with(record["body"])

     @sqs_batch_processor(record_handler=record_handler)
     def lambda_handler(event, context):
         return {"statusCode": 200}
     ```

=== "Decorator: After"

     ```python hl_lines="3 5 11"
     import json

     from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor

     processor = BatchProcessor(event_type=EventType.SQS)


     def record_handler(record):
         return do_something_with(record["body"])

     @batch_processor(record_handler=record_handler, processor=processor)
     def lambda_handler(event, context):
         return processor.response()
     ```

=== "Context manager: Before"

     ```python hl_lines="1-2 4 14 19"
     from aws_lambda_powertools.utilities.batch import PartialSQSProcessor
     from botocore.config import Config

     config = Config(region_name="us-east-1")

     def record_handler(record):
         return_value = do_something_with(record["body"])
         return return_value


     def lambda_handler(event, context):
         records = event["Records"]

         processor = PartialSQSProcessor(config=config)

         with processor(records, record_handler):
             result = processor.process()

         return result
     ```

=== "Context manager: After"

    ```python hl_lines="1 11"
    from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor


    def record_handler(record):
        return_value = do_something_with(record["body"])
        return return_value

    def lambda_handler(event, context):
        records = event["Records"]

        processor = BatchProcessor(event_type=EventType.SQS)

        with processor(records, record_handler):
            result = processor.process()

        return processor.response()
    ```

## Event Handler Response (headers and cookies)

The `Response` class of the event handler utility changed slightly:

1. The `headers` parameter now expects either a value or list of values per header (type `Union[str, Dict[str, List[str]]]`)
2. We introduced a new `cookies` parameter (type `List[str]`)

???+ note
    Code that set headers as `Dict[str, str]` will still work unchanged.

```python hl_lines="6 12 13"
@app.get("/todos")
def get_todos():
    # Before
    return Response(
        # ...
        headers={"Content-Type": "text/plain"}
    )

    # After
    return Response(
        # ...
        headers={"Content-Type": ["text/plain"]},
        cookies=[Cookie(name="session_id", value="12345", secure=True, http_only=True)],
    )
```

## DynamoDBStreamEvent in Event Source Data Classes

???+ info
    This also applies if you're using [**`BatchProcessor`**](https://awslabs.github.io/aws-lambda-powertools-python/latest/utilities/batch/#processing-messages-from-dynamodb){target="_blank"} to handle DynamoDB Stream events.

You will now receive native Python types when accessing DynamoDB records via `keys`, `new_image`, and `old_image` attributes in `DynamoDBStreamEvent`.

Previously, you'd receive a `AttributeValue` instance and need to deserialize each item to the type you'd want for convenience, or to the type DynamoDB stored via `get_value` method.

With this change, you can access data deserialized as stored in DynamoDB, and no longer need to recursively deserialize nested objects (Maps) if you had them.

???+ note
    For a lossless conversion of DynamoDB `Number` type, we follow AWS Python SDK (boto3) approach and convert to `Decimal`.

```python hl_lines="15-20 24-25"
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBStreamEvent,
    DynamoDBRecordEventName
)

def send_to_sqs(data: Dict):
    body = json.dumps(data)
    ...

@event_source(data_class=DynamoDBStreamEvent)
def lambda_handler(event: DynamoDBStreamEvent, context):
    for record in event.records:

        # BEFORE
        new_image: Dict[str, AttributeValue] = record.dynamodb.new_image
        event_type: AttributeValue = new_image["eventType"].get_value
        if event_type == "PENDING":
            # deserialize attribute value into Python native type
            # NOTE: nested objects would need additional logic
            data = {k: v.get_value for k, v in image.items()}
            send_to_sqs(data)

        # AFTER
        new_image: Dict[str, Any] = record.dynamodb.new_image
        if new_image.get("eventType") == "PENDING":
            send_to_sqs(new_image)  # Here new_image is just a Python Dict type

```

## Feature Flags and AppConfig Parameter utility

???+ info
    AWS AppConfig deprecated the current API (GetConfiguration) - [more details here](https://github.com/awslabs/aws-lambda-powertools-python/issues/1506#issuecomment-1266645884).

You must update your IAM permissions to allow `appconfig:GetLatestConfiguration` and `appconfig:StartConfigurationSession`. There are no code changes required.

## Idempotency key format

???+ note
    Using qualified names prevents distinct functions with the same name to contend for the same Idempotency key.

The format of the Idempotency key was changed. This is used store the invocation results on a persistent store like DynamoDB.

No changes are necessary in your code, but remember that existing Idempotency records will be ignored when you upgrade, as new executions generate keys with the new format.

Prior to this change, the Idempotency key was generated using only the caller function name (e.g: `HelloWorldFunction.lambda_handler#99914b932bd37a50b983c5e7c90ae93b`).

![Idempotency Before](./media/upgrade_idempotency_before.png)

After this change, the key is generated using the `module name` + `qualified function name` + `idempotency key` (e.g: `HelloWorldFunction.app.lambda_handler#99914b932bd37a50b983c5e7c90ae93b`).

![Idempotency Before](./media/upgrade_idempotency_after.png)
