---
title: SQS Batch Processing
description: Utility
---

import Note from "../../src/components/Note"

The SQS batch processing utility provides a way to handle partial failures when processing batches of messages from SQS.

**Key Features**

* Prevent successfully processed messages being returned to SQS
* Simple interface for individually processing messages from a batch
* Build your own batch processor using the base classes

**Background**

When using SQS as a Lambda event source mapping, Lambda functions are triggered with a batch of messages from SQS.

If your function fails to process any message from the batch, the entire batch returns to your SQS queue, and your Lambda function is triggered with the same batch one more time.

With this utility, messages within a batch are handled individually - only messages that were not successfully processed
are returned to the queue.

<Note type="warning">
  While this utility lowers the chance of processing messages more than once, it is not guaranteed. We recommend implementing processing logic in an idempotent manner wherever possible.
  <br/><br/>
  More details on how Lambda works with SQS can be found in the <a href="https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html">AWS documentation</a>
</Note><br/>


**IAM Permissions**

This utility requires additional permissions to work as expected. Lambda functions using this utility require the `sqs:DeleteMessageBatch` permission.

## Processing messages from SQS

You can use either **[sqs_batch_processor](#sqs_batch_processor-decorator)** decorator, or **[PartialSQSProcessor](#partialsqsprocessor-context-manager)** as a context manager.

They have nearly the same behaviour when it comes to processing messages from the batch:

* **Entire batch has been successfully processed**, where your Lambda handler returned successfully, we will let SQS delete the batch to optimize your cost
* **Entire Batch has been partially processed successfully**, where exceptions were raised within your `record handler`, we will:
    - **1)** Delete successfully processed messages from the queue by directly calling `sqs:DeleteMessageBatch`
    - **2)** Raise `SQSBatchProcessingError` to ensure failed messages return to your SQS queue

The only difference is that **PartialSQSProcessor** will give you access to processed messages if you need.

## Record Handler

Both decorator and context managers require an explicit function to process the batch of messages - namely `record_handler` parameter.

This function is responsible for processing each individual message from the batch, and to raise an exception if unable to process any of the messages sent.

**Any non-exception/successful return from your record handler function** will instruct both decorator and context manager to queue up each individual message for deletion.

### sqs_batch_processor decorator

When using the this decorator, you need provide a function via `record_handler` param that will process individual messages from the batch - It should raise an exception if it is unable to process the record.

All records in the batch will be passed to this handler for processing, even if exceptions are thrown - Here's the behaviour after completing the batch:

* **Any successfully processed messages**, we will delete them from the queue via `sqs:DeleteMessageBatch`
* **Any unprocessed messages detected**, we will raise `SQSBatchProcessingError` to ensure failed messages return to your SQS queue

<Note type="warning">
  You will not have accessed to the <strong>processed messages</strong> within the Lambda Handler - all processing logic will and should be performed by the <code>record_handler</code> function.
</Note><br/>

```python:title=app.py
from aws_lambda_powertools.utilities.batch import sqs_batch_processor

def record_handler(record):
    # This will be called for each individual message from a batch
    # It should raise an exception if the message was not processed successfully
    return_value = do_something_with(record["body"])
    return return_value

@sqs_batch_processor(record_handler=record_handler)
def lambda_handler(event, context):
    return {"statusCode": 200}
```

### PartialSQSProcessor context manager

If you require access to the result of processed messages, you can use this context manager.

The result from calling `process()` on the context manager will be a list of all the return values from your `record_handler` function.

```python:title=app.py
from aws_lambda_powertools.utilities.batch import PartialSQSProcessor

def record_handler(record):
    # This will be called for each individual message from a batch
    # It should raise an exception if the message was not processed successfully
    return_value = do_something_with(record["body"])
    return return_value


def lambda_handler(event, context):
    records = event["Records"]

    processor = PartialSQSProcessor()

    with processor(records, record_handler) as proc:
        result = proc.process()  # Returns a list of all results from record_handler

    return result
```

## Passing custom boto3 config

If you need to pass custom configuration such as region to the SDK, you can pass your own [botocore config object](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html) to
the `sqs_batch_processor` decorator:

```python:title=app.py
from aws_lambda_powertools.utilities.batch import sqs_batch_processor
from botocore.config import Config

config = Config(region_name="us-east-1")  # highlight-line

def record_handler(record):
    # This will be called for each individual message from a batch
    # It should raise an exception if the message was not processed successfully
    return_value = do_something_with(record["body"])
    return return_value

@sqs_batch_processor(record_handler=record_handler, config=config)  # highlight-line
def lambda_handler(event, context):
    return {"statusCode": 200}
```

Or to the `PartialSQSProcessor` class:
```python:title=app.py
from aws_lambda_powertools.utilities.batch import PartialSQSProcessor

from botocore.config import Config

config = Config(region_name="us-east-1")  # highlight-line

def record_handler(record):
    # This will be called for each individual message from a batch
    # It should raise an exception if the message was not processed successfully
    return_value = do_something_with(record["body"])
    return return_value


def lambda_handler(event, context):
    records = event["Records"]

    processor = PartialSQSProcessor(config=config)  # highlight-line

    with processor(records, record_handler):
        result = processor.process()

    return result
```


## Suppressing exceptions

If you want to disable the default behavior where `SQSBatchProcessingError` is raised if there are any errors, you can pass the `suppress_exception` boolean argument.

**Within the decorator**

```python:title=app.py
...
@sqs_batch_processor(record_handler=record_handler, config=config, suppress_exception=True)  # highlight-line
def lambda_handler(event, context):
    return {"statusCode": 200}
```

**Within the context manager**

```python:title=app.py
processor = PartialSQSProcessor(config=config, suppress_exception=True)  # highlight-line

with processor(records, record_handler):
    result = processor.process()
```

## Create your own partial processor

You can create your own partial batch processor by inheriting the `BasePartialProcessor` class, and implementing `_prepare()`, `_clean()` and `_process_record()`.

* **`_process_record()`** - Handles all processing logic for each individual message of a batch, including calling the `record_handler` (self.handler)
* **`_prepare()`** - Called once as part of the processor initialization
* **`clean()`** - Teardown logic called once after `_process_record` completes

You can then use this class as a context manager, or pass it to `batch_processor` to use as a decorator on your Lambda handler function.

**Example:**

```python:title=custom_processor.py
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
        # E.g.:
        self.ddb_table = boto3.resource("dynamodb").Table(self.table_name)
        self.success_messages.clear()

    def _clean(self):
        # It's called once, *after* closing processing all records (closing the context manager)
        # Here we're sending, at once, all successful messages to a ddb table
        # E.g.:
        with ddb_table.batch_writer() as batch:
            for result in self.success_messages:
                batch.put_item(Item=result)

    def _process_record(self, record):
        # It handles how your record is processed
        # Here we're keeping the status of each run
        # where self.handler is the record_handler function passed as an argument
        # E.g.:
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
