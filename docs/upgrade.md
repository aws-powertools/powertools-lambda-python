---
title: Upgrade guide
description: Guide to update between major Powertools versions
---

<!-- markdownlint-disable MD043 -->

## Migrate to v2 from v1

The transition from Powertools for Python v1 to v2 is as painless as possible, as we aimed for minimal breaking changes.
Changes at a glance:

* The API for **event handler's `Response`** has minor changes to support multi value headers and cookies.
* The **legacy SQS batch processor** was removed.
* The **Idempotency key** format changed slightly, invalidating all the existing cached results.
* The **Feature Flags and AppConfig Parameter utility** API calls have changed and you must update your IAM permissions.

???+ important
    Powertools for Python v2 drops suport for Python 3.6, following the Python 3.6 End-Of-Life (EOL) reached on December 23, 2021.

### Initial Steps

Before you start, we suggest making a copy of your current working project or create a new branch with git.

1. **Upgrade** Python to at least v3.7

2. **Ensure** you have the latest `aws-lambda-powertools`

    ```bash
    pip install aws-lambda-powertools -U
    ```

3. **Review** the following sections to confirm whether they affect your code

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

## Idempotency key format

The format of the Idempotency key was changed. This is used store the invocation results on a persistent store like DynamoDB.

No changes are necessary in your code, but remember that existing Idempotency records will be ignored when you upgrade, as new executions generate keys with the new format.

Prior to this change, the Idempotency key was generated using only the caller function name (e.g: `lambda_handler#282e83393862a613b612c00283fef4c8`).
After this change, the key is generated using the `module name` + `qualified function name` + `idempotency key` (e.g: `app.classExample.function#app.handler#282e83393862a613b612c00283fef4c8`).

Using qualified names prevents distinct functions with the same name to contend for the same Idempotency key.

## Feature Flags and AppConfig Parameter utility

AWS AppConfig deprecated the current API (GetConfiguration) - [more details here](https://github.com/awslabs/aws-lambda-powertools-python/issues/1506#issuecomment-1266645884).

You must update your IAM permissions to allow `appconfig:GetLatestConfiguration` and `appconfig:StartConfigurationSession`. There are no code changes required.
