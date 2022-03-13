---
title: Idempotency
description: Utility
---

The idempotency utility provides a simple solution to convert your Lambda functions into idempotent operations which
are safe to retry.

## Terminology

The property of idempotency means that an operation does not cause additional side effects if it is called more than
once with the same input parameters.

**Idempotent operations will return the same result when they are called multiple
times with the same parameters**. This makes idempotent operations safe to retry.

**Idempotency key** is a hash representation of either the entire event or a specific configured subset of the event, and invocation results are **JSON serialized** and stored in your persistence storage layer.

## Key features

* Prevent Lambda handler from executing more than once on the same event payload during a time window
* Ensure Lambda handler returns the same result when called with the same payload
* Select a subset of the event as the idempotency key using JMESPath expressions
* Set a time window in which records with the same payload should be considered duplicates

## Getting started

### Required resources

Before getting started, you need to create a persistent storage layer where the idempotency utility can store its state - your lambda functions will need read and write access to it.

As of now, Amazon DynamoDB is the only supported persistent storage layer, so you'll need to create a table first.

**Default table configuration**

If you're not [changing the default configuration for the DynamoDB persistence layer](#dynamodbpersistencelayer), this is the expected default configuration:

Configuration | Value | Notes
------------------------------------------------- | ------------------------------------------------- | -------------------------------------------------
Partition key | `id` |
TTL attribute name | `expiration` | This can only be configured after your table is created if you're using AWS Console

???+ tip "Tip: You can share a single state table for all functions"
    You can reuse the same DynamoDB table to store idempotency state. We add your `function_name` in addition to the idempotency key as a hash key.

```yaml hl_lines="7-15 24-26" title="AWS Serverless Application Model (SAM) example"
--8<-- "docs/examples/utilities/idempotency/template.yml"
```

???+ warning "Warning: Large responses with DynamoDB persistence layer"
    When using this utility with DynamoDB, your function's responses must be [smaller than 400KB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Limits.html#limits-items).

    Larger items cannot be written to DynamoDB and will cause exceptions.

???+ info "Info: DynamoDB"
    Each function invocation will generally make 2 requests to DynamoDB. If the
    result returned by your Lambda is less than 1kb, you can expect 2 WCUs per invocation. For retried invocations, you will
    see 1WCU and 1RCU. Review the [DynamoDB pricing documentation](https://aws.amazon.com/dynamodb/pricing/) to
    estimate the cost.

### Idempotent decorator

You can quickly start by initializing the `DynamoDBPersistenceLayer` class and using it with the `idempotent` decorator on your lambda handler.

=== "app.py"

    ```python hl_lines="1 3 6 10"
    --8<-- "docs/examples/utilities/idempotency/idempotent_decorator.py"
    ```

=== "Example event"

    ```json
    {
      "username": "xyz",
      "product_id": "123456789"
    }
    ```

### Idempotent function decorator

Similar to [idempotent decorator](#idempotent-decorator), you can use `idempotent_function` decorator for any synchronous Python function.

When using `idempotent_function`, you must tell us which keyword parameter in your function signature has the data we should use via **`data_keyword_argument`**.

!!! info "We support JSON serializable data, [Python Dataclasses](https://docs.python.org/3.7/library/dataclasses.html){target="_blank"}, [Parser/Pydantic Models](parser.md){target="_blank"}, and our [Event Source Data Classes](./data_classes.md){target="_blank"}."

???+ warning
    Make sure to call your decorated function using keyword arguments

=== "batch_sample.py"

    This example also demonstrates how you can integrate with [Batch utility](batch.md), so you can process each record in an idempotent manner.

    ```python hl_lines="3 13 18 26"
    --8<-- "docs/examples/utilities/idempotency/batch_sample.py"
    ```

=== "Batch event"

    ```json hl_lines="4"
    {
        "Records": [
            {
                "messageId": "059f36b4-87a3-44ab-83d2-661975830a7d",
                "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a...",
                "body": "Test message.",
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1545082649183",
                    "SenderId": "AIDAIENQZJOLO23YVJ4VO",
                    "ApproximateFirstReceiveTimestamp": "1545082649185"
                },
                "messageAttributes": {
                    "testAttr": {
                    "stringValue": "100",
                    "binaryValue": "base64Str",
                    "dataType": "Number"
                    }
                },
                "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-2:123456789012:my-queue",
                "awsRegion": "us-east-2"
            }
        ]
    }
    ```

=== "dataclass_sample.py"

    ```python hl_lines="3 24 33"
    --8<-- "docs/examples/utilities/idempotency/dataclass_sample.py"
    ```

=== "parser_pydantic_sample.py"

    ```python hl_lines="1 21 30"
    --8<-- "docs/examples/utilities/idempotency/parser_pydantic_sample.py"
    ```

### Choosing a payload subset for idempotency

???+ tip "Tip: Dealing with always changing payloads"
    When dealing with a more elaborate payload, where parts of the payload always change, you should use **`event_key_jmespath`** parameter.

Use [`IdempotencyConfig`](#customizing-the-default-behavior) to instruct the idempotent decorator to only use a portion of your payload to verify whether a request is idempotent, and therefore it should not be retried.

> **Payment scenario**

In this example, we have a Lambda handler that creates a payment for a user subscribing to a product. We want to ensure that we don't accidentally charge our customer by subscribing them more than once.

Imagine the function executes successfully, but the client never receives the response due to a connection issue. It is safe to retry in this instance, as the idempotent decorator will return a previously saved response.

???+ warning "Warning: Idempotency for JSON payloads"
    The payload extracted by the `event_key_jmespath` is treated as a string by default, so will be sensitive to differences in whitespace even when the JSON payload itself is identical.

    To alter this behaviour, we can use the [JMESPath built-in function](jmespath_functions.md#powertools_json-function) `powertools_json()` to treat the payload as a JSON object (dict) rather than a string.

=== "payment.py"

    ```python hl_lines="3 9 12 15 20"
    --8<-- "docs/examples/utilities/idempotency/payment.py"
    ```

=== "Example event"

    ```json hl_lines="28"
    {
      "version":"2.0",
      "routeKey":"ANY /createpayment",
      "rawPath":"/createpayment",
      "rawQueryString":"",
      "headers": {
        "Header1": "value1",
        "Header2": "value2"
      },
      "requestContext":{
        "accountId":"123456789012",
        "apiId":"api-id",
        "domainName":"id.execute-api.us-east-1.amazonaws.com",
        "domainPrefix":"id",
        "http":{
          "method":"POST",
          "path":"/createpayment",
          "protocol":"HTTP/1.1",
          "sourceIp":"ip",
          "userAgent":"agent"
        },
        "requestId":"id",
        "routeKey":"ANY /createpayment",
        "stage":"$default",
        "time":"10/Feb/2021:13:40:43 +0000",
        "timeEpoch":1612964443723
      },
      "body":"{\"user\":\"xyz\",\"product_id\":\"123456789\"}",
      "isBase64Encoded":false
    }
    ```


### Idempotency request flow

This sequence diagram shows an example flow of what happens in the payment scenario:

![Idempotent sequence](../media/idempotent_sequence.png)

The client was successful in receiving the result after the retry. Since the Lambda handler was only executed once, our customer hasn't been charged twice.

???+ note
    Bear in mind that the entire Lambda handler is treated as a single idempotent operation. If your Lambda handler can cause multiple side effects, consider splitting it into separate functions.

### Handling exceptions

If you are using the `idempotent` decorator on your Lambda handler, any unhandled exceptions that are raised during the code execution will cause **the record in the persistence layer to be deleted**.
This means that new invocations will execute your code again despite having the same payload. If you don't want the record to be deleted, you need to catch exceptions within the idempotent function and return a successful response.

![Idempotent sequence exception](../media/idempotent_sequence_exception.png)

If you are using `idempotent_function`, any unhandled exceptions that are raised _inside_ the decorated function will cause the record in the persistence layer to be deleted, and allow the function to be executed again if retried.

If an Exception is raised _outside_ the scope of the decorated function and after your function has been called, the persistent record will not be affected. In this case, idempotency will be maintained for your decorated function. Example:

```python hl_lines="10-12 16-18" title="Exception not affecting idempotency record sample"
--8<-- "docs/examples/utilities/idempotency/idempotency_exception_sample.py"
```

???+ warning
    **We will raise `IdempotencyPersistenceLayerError`** if any of the calls to the persistence layer fail unexpectedly.

    As this happens outside the scope of your decorated function, you are not able to catch it if you're using the `idempotent` decorator on your Lambda handler.

### Persistence layers

#### DynamoDBPersistenceLayer

This persistence layer is built-in, and you can either use an existing DynamoDB table or create a new one dedicated for idempotency state (recommended).

```python hl_lines="5-9" title="Customizing DynamoDBPersistenceLayer to suit your table structure"
--8<-- "docs/examples/utilities/idempotency/dynamodb_persistence_layer_customization.py"
```

When using DynamoDB as a persistence layer, you can alter the attribute names by passing these parameters when initializing the persistence layer:

Parameter | Required | Default | Description
------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------
**table_name** | :heavy_check_mark: | | Table name to store state
**key_attr** |  | `id` | Partition key of the table. Hashed representation of the payload (unless **sort_key_attr** is specified)
**expiry_attr** |  | `expiration` | Unix timestamp of when record expires
**status_attr** |  | `status` | Stores status of the lambda execution during and after invocation
**data_attr** |  | `data`  | Stores results of successfully executed Lambda handlers
**validation_key_attr** |  | `validation` | Hashed representation of the parts of the event used for validation
**sort_key_attr** | | | Sort key of the table (if table is configured with a sort key).
**static_pk_value** | | `idempotency#{LAMBDA_FUNCTION_NAME}` | Static value to use as the partition key. Only used when **sort_key_attr** is set.

## Advanced

### Customizing the default behavior

Idempotent decorator can be further configured with **`IdempotencyConfig`** as seen in the previous example. These are the available options for further configuration

Parameter | Default | Description
------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------
**event_key_jmespath** | `""` | JMESPath expression to extract the idempotency key from the event record using [built-in functions](/utilities/jmespath_functions)
**payload_validation_jmespath** | `""` | JMESPath expression to validate whether certain parameters have changed in the event while the event payload
**raise_on_no_idempotency_key** | `False` | Raise exception if no idempotency key was found in the request
**expires_after_seconds** | 3600 | The number of seconds to wait before a record is expired
**use_local_cache** | `False` | Whether to locally cache idempotency results
**local_cache_max_items** | 256 | Max number of items to store in local cache
**hash_function** | `md5` | Function to use for calculating hashes, as provided by [hashlib](https://docs.python.org/3/library/hashlib.html) in the standard library.

### Handling concurrent executions with the same payload

This utility will raise an **`IdempotencyAlreadyInProgressError`** exception if you receive **multiple invocations with the same payload while the first invocation hasn't completed yet**.

???+ info
    If you receive `IdempotencyAlreadyInProgressError`, you can safely retry the operation.

This is a locking mechanism for correctness. Since we don't know the result from the first invocation yet, we can't safely allow another concurrent execution.

### Using in-memory cache

**By default, in-memory local caching is disabled**, since we don't know how much memory you consume per invocation compared to the maximum configured in your Lambda function.

???+ note "Note: This in-memory cache is local to each Lambda execution environment"
    This means it will be effective in cases where your function's concurrency is low in comparison to the number of "retry" invocations with the same payload, because cache might be empty.

You can enable in-memory caching with the **`use_local_cache`** parameter:

```python hl_lines="6 10" title="Caching idempotent transactions in-memory to prevent multiple calls to storage"
--8<-- "docs/examples/utilities/idempotency/idempotency_in_memory_cache.py"
```

When enabled, the default is to cache a maximum of 256 records in each Lambda execution environment - You can change it with the **`local_cache_max_items`** parameter.

### Expiring idempotency records

???+ note
    By default, we expire idempotency records after **an hour** (3600 seconds).

In most cases, it is not desirable to store the idempotency records forever. Rather, you want to guarantee that the same payload won't be executed within a period of time.

You can change this window with the **`expires_after_seconds`** parameter:

```python hl_lines="6 10" title="Adjusting cache TTL"
--8<-- "docs/examples/utilities/idempotency/idempotency_cache_ttl.py"
```

This will mark any records older than 5 minutes as expired, and the lambda handler will be executed as normal if it is invoked with a matching payload.

???+ note "Note: DynamoDB time-to-live field"
    This utility uses **`expiration`** as the TTL field in DynamoDB, as [demonstrated in the SAM example earlier](#required-resources).

### Payload validation

???+ question "Question: What if your function is invoked with the same payload except some outer parameters have changed?"
    Example: A payment transaction for a given productID was requested twice for the same customer, **however the amount to be paid has changed in the second transaction**.

By default, we will return the same result as it returned before, however in this instance it may be misleading; we provide a fail fast payload validation to address this edge case.

With **`payload_validation_jmespath`**, you can provide an additional JMESPath expression to specify which part of the event body should be validated against previous idempotent invocations

=== "app.py"

    ```python hl_lines="5 10 17 24"
    --8<-- "docs/examples/utilities/idempotency/idempotency_payload_validation.py"
    ```

=== "Example Event 1"

    ```json hl_lines="8"
    {
        "userDetail": {
            "username": "User1",
            "user_email": "user@example.com"
        },
        "productId": 1500,
        "charge_type": "subscription",
        "amount": 500
    }
    ```

=== "Example Event 2"

    ```json hl_lines="8"
    {
        "userDetail": {
            "username": "User1",
            "user_email": "user@example.com"
        },
        "productId": 1500,
        "charge_type": "subscription",
        "amount": 1
    }
    ```

In this example, the **`userDetail`** and **`productId`** keys are used as the payload to generate the idempotency key, as per **`event_key_jmespath`** parameter.

???+ note
    If we try to send the same request but with a different amount, we will raise **`IdempotencyValidationError`**.

Without payload validation, we would have returned the same result as we did for the initial request. Since we're also returning an amount in the response, this could be quite confusing for the client.

By using **`payload_validation_jmespath="amount"`**, we prevent this potentially confusing behavior and instead raise an Exception.

### Making idempotency key required

If you want to enforce that an idempotency key is required, you can set **`raise_on_no_idempotency_key`** to `True`.

This means that we will raise **`IdempotencyKeyError`** if the evaluation of **`event_key_jmespath`** is `None`.

=== "app.py"

    ```python hl_lines="7-8 12"
    --8<-- "docs/examples/utilities/idempotency/idempotency_key_required.py"
    ```

=== "Success Event"

    ```json hl_lines="3 6"
    {
        "user": {
            "uid": "BB0D045C-8878-40C8-889E-38B3CB0A61B1",
            "name": "Foo"
        },
        "order_id": 10000
    }
    ```

=== "Failure Event"

    Notice that `order_id` is now accidentally within `user` key

    ```json hl_lines="3 5"
    {
        "user": {
            "uid": "DE0D000E-1234-10D1-991E-EAC1DD1D52C8",
            "name": "Joe Bloggs",
            "order_id": 10000
        },
    }
    ```

### Customizing boto configuration

The **`boto_config`** and **`boto3_session`** parameters enable you to pass in a custom [botocore config object](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html) or a custom [boto3 session](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html) when constructing the persistence store.

=== "Custom session"

    ```python hl_lines="1 5 8 14"
    --8<-- "docs/examples/utilities/idempotency/idempotency_custom_session.py"
    ```

=== "Custom config"

    ```python hl_lines="1 6 9 13"
    --8<-- "docs/examples/utilities/idempotency/idempotency_custom_config.py"
    ```

### Using a DynamoDB table with a composite primary key

When using a composite primary key table (hash+range key), use `sort_key_attr` parameter when initializing your persistence layer.

With this setting, we will save the idempotency key in the sort key instead of the primary key. By default, the primary key will now be set to `idempotency#{LAMBDA_FUNCTION_NAME}`.

You can optionally set a static value for the partition key using the `static_pk_value` parameter.

```python hl_lines="5" title="Reusing a DynamoDB table that uses a composite primary key"
--8<-- "docs/examples/utilities/idempotency/idempotency_composite_primary_key.py"
```

The example function above would cause data to be stored in DynamoDB like this:

| id                           | sort_key                         | expiration | status      | data                                |
|------------------------------|----------------------------------|------------|-------------|-------------------------------------|
| idempotency#MyLambdaFunction | 1e956ef7da78d0cb890be999aecc0c9e | 1636549553 | COMPLETED   | {"id": 12391, "message": "success"} |
| idempotency#MyLambdaFunction | 2b2cdb5f86361e97b4383087c1ffdf27 | 1636549571 | COMPLETED   | {"id": 527212, "message": "success"}|
| idempotency#MyLambdaFunction | f091d2527ad1c78f05d54cc3f363be80 | 1636549585 | IN_PROGRESS |                                     |

### Bring your own persistent store

This utility provides an abstract base class (ABC), so that you can implement your choice of persistent storage layer.

You can inherit from the `BasePersistenceLayer` class and implement the abstract methods `_get_record`, `_put_record`,
`_update_record` and `_delete_record`.

```python hl_lines="8-13 57 65 74 96 124" title="Excerpt DynamoDB Persisntence Layer implementation for reference"
--8<-- "docs/examples/utilities/idempotency/bring_your_own_persistent_store.py"
```

???+ danger
    Pay attention to the documentation for each - you may need to perform additional checks inside these methods to ensure the idempotency guarantees remain intact.

    For example, the `_put_record` method needs to raise an exception if a non-expired record already exists in the data store with a matching key.

## Compatibility with other utilities

### Validation utility

The idempotency utility can be used with the `validator` decorator. Ensure that idempotency is the innermost decorator.

???+ warning
    If you use an envelope with the validator, the event received by the idempotency utility will be the unwrapped
    event - not the "raw" event Lambda was invoked with.

	Make sure to account for this behaviour, if you set the `event_key_jmespath`.

```python hl_lines="9 10" title="Using Idempotency with JSONSchema Validation utility"
from aws_lambda_powertools.utilities.validation import validator, envelopes
from aws_lambda_powertools.utilities.idempotency import (
	IdempotencyConfig, DynamoDBPersistenceLayer, idempotent
)

config = IdempotencyConfig(event_key_jmespath="[message, username]")
persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")

@validator(envelope=envelopes.API_GATEWAY_HTTP)
@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
	cause_some_side_effects(event['username')
	return {"message": event['message'], "statusCode": 200}
```

???+ tip "Tip: JMESPath Powertools functions are also available"
    Built-in functions known in the validation utility like `powertools_json`, `powertools_base64`, `powertools_base64_gzip` are also available to use in this utility.


## Testing your code

The idempotency utility provides several routes to test your code.

### Disabling the idempotency utility
When testing your code, you may wish to disable the idempotency logic altogether and focus on testing your business logic. To do this, you can set the environment variable `POWERTOOLS_IDEMPOTENCY_DISABLED`
with a truthy value. If you prefer setting this for specific tests, and are using Pytest, you can use [monkeypatch](https://docs.pytest.org/en/latest/monkeypatch.html) fixture:

=== "tests.py"

    ```python hl_lines="2 3"
    def test_idempotent_lambda_handler(monkeypatch):
        # Set POWERTOOLS_IDEMPOTENCY_DISABLED before calling decorated functions
        monkeypatch.setenv("POWERTOOLS_IDEMPOTENCY_DISABLED", 1)

        result = handler()
        ...
    ```
=== "app.py"

    ```python
    from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer, idempotent
    )

    persistence_layer = DynamoDBPersistenceLayer(table_name="idempotency")

    @idempotent(persistence_store=persistence_layer)
    def handler(event, context):
        print('expensive operation')
        return {
            "payment_id": 12345,
            "message": "success",
            "statusCode": 200,
        }
    ```

### Testing with DynamoDB Local

To test with [DynamoDB Local](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html), you can replace the `Table` resource used by the persistence layer with one you create inside your tests. This allows you to set the endpoint_url.

=== "tests.py"

    ```python hl_lines="6 7 8"
    import boto3

    import app

    def test_idempotent_lambda():
        # Create our own Table resource using the endpoint for our DynamoDB Local instance
        resource = boto3.resource("dynamodb", endpoint_url='http://localhost:8000')
        table = resource.Table(app.persistence_layer.table_name)
        app.persistence_layer.table = table

        result = app.handler({'testkey': 'testvalue'}, {})
        assert result['payment_id'] == 12345
    ```

=== "app.py"

    ```python
    from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer, idempotent
    )

    persistence_layer = DynamoDBPersistenceLayer(table_name="idempotency")

    @idempotent(persistence_store=persistence_layer)
    def handler(event, context):
        print('expensive operation')
        return {
            "payment_id": 12345,
            "message": "success",
            "statusCode": 200,
        }
    ```

### How do I mock all DynamoDB I/O operations

The idempotency utility lazily creates the dynamodb [Table](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#table) which it uses to access DynamoDB.
This means it is possible to pass a mocked Table resource, or stub various methods.

=== "tests.py"

    ```python hl_lines="6 7 8 9"
    from unittest.mock import MagicMock

    import app

    def test_idempotent_lambda():
        table = MagicMock()
        app.persistence_layer.table = table
        result = app.handler({'testkey': 'testvalue'}, {})
        table.put_item.assert_called()
        ...
    ```

=== "app.py"

    ```python
    from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer, idempotent
    )

    persistence_layer = DynamoDBPersistenceLayer(table_name="idempotency")

    @idempotent(persistence_store=persistence_layer)
    def handler(event, context):
        print('expensive operation')
        return {
            "payment_id": 12345,
            "message": "success",
            "statusCode": 200,
        }
    ```

## Extra resources

If you're interested in a deep dive on how Amazon uses idempotency when building our APIs, check out
[this article](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).
