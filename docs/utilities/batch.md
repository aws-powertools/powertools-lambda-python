---
title: SQS Batch Processing
description: Utility
---

The SQS batch processing utility provides a way to handle partial failures when processing batches of messages from SQS.

## Key Features

* Prevent successfully processed messages being returned to SQS
* Simple interface for individually processing messages from a batch
* Build your own batch processor using the base classes

## Background

When using SQS as a Lambda event source mapping, Lambda functions are triggered with a batch of messages from SQS.

If your function fails to process any message from the batch, the entire batch returns to your SQS queue, and your Lambda function is triggered with the same batch one more time.

With this utility, messages within a batch are handled individually - only messages that were not successfully processed
are returned to the queue.

!!! warning
    While this utility lowers the chance of processing messages more than once, it is not guaranteed. We recommend implementing processing logic in an idempotent manner wherever possible.

    More details on how Lambda works with SQS can be found in the [AWS documentation](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)

## Getting started

### IAM Permissions

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

You can use either **[sqs_batch_processor](#sqs_batch_processor-decorator)** decorator, or **[PartialSQSProcessor](#partialsqsprocessor-context-manager)** as a context manager if you'd like access to the processed results.

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

	If the entire batch succeeds, we let Lambda to proceed in deleting the records from the queue for cost reasons.

### Partial failure mechanics

All records in the batch will be passed to this handler for processing, even if exceptions are thrown - Here's the behaviour after completing the batch:

* **Any successfully processed messages**, we will delete them from the queue via `sqs:DeleteMessageBatch`
* **Any unprocessed messages detected**, we will raise `SQSBatchProcessingError` to ensure failed messages return to your SQS queue

!!! warning
    You will not have accessed to the **processed messages** within the Lambda Handler.

	All processing logic will and should be performed by the `record_handler` function.

## Advanced

### Choosing between decorator and context manager

They have nearly the same behaviour when it comes to processing messages from the batch:

* **Entire batch has been successfully processed**, where your Lambda handler returned successfully, we will let SQS delete the batch to optimize your cost
* **Entire Batch has been partially processed successfully**, where exceptions were raised within your `record handler`, we will:
    - **1)** Delete successfully processed messages from the queue by directly calling `sqs:DeleteMessageBatch`
    - **2)** Raise `SQSBatchProcessingError` to ensure failed messages return to your SQS queue

The only difference is that **PartialSQSProcessor** will give you access to processed messages if you need.

### Accessing processed messages

Use `PartialSQSProcessor` context manager to access a list of all return values from your `record_handler` function.

=== "app.py"

    ```python
    from aws_lambda_powertools.utilities.batch import PartialSQSProcessor

    def record_handler(record):
        return do_something_with(record["body"])

    def lambda_handler(event, context):
        records = event["Records"]

        processor = PartialSQSProcessor()

        with processor(records, record_handler) as proc:
            result = proc.process()  # Returns a list of all results from record_handler

        return result
    ```

### Passing custom boto3 config

If you need to pass custom configuration such as region to the SDK, you can pass your own [botocore config object](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html) to
the `sqs_batch_processor` decorator:

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

### Create your own partial processor

You can create your own partial batch processor by inheriting the `BasePartialProcessor` class, and implementing `_prepare()`, `_clean()` and `_process_record()`.

* **`_process_record()`** - Handles all processing logic for each individual message of a batch, including calling the `record_handler` (self.handler)
* **`_prepare()`** - Called once as part of the processor initialization
* **`clean()`** - Teardown logic called once after `_process_record` completes

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

### Integrating exception handling with Sentry.io

When using Sentry.io for error monitoring, you can override `failure_handler` to include to capture each processing exception:

> Credits to [Charles-Axel Dein](https://github.com/awslabs/aws-lambda-powertools-python/issues/293#issuecomment-781961732)

=== "sentry_integration.py"

	```python hl_lines="4 7-8"
	from typing import Tuple

	from aws_lambda_powertools.utilities.batch import PartialSQSProcessor
	from sentry_sdk import capture_exception

	class SQSProcessor(PartialSQSProcessor):
		def failure_handler(self, record: Event, exception: Tuple) -> Tuple:  # type: ignore
			capture_exception()  # send exception to Sentry
			logger.exception("got exception while processing SQS message")
			return super().failure_handler(record, exception)  # type: ignore
	```
