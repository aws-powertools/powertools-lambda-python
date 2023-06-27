---
title: Idempotency
description: Utility
---

<!-- markdownlint-disable MD051 -->

The idempotency utility provides a simple solution to convert your Lambda functions into idempotent operations which are safe to retry.

## Key features

* Prevent Lambda handler from executing more than once on the same event payload during a time window
* Ensure Lambda handler returns the same result when called with the same payload
* Select a subset of the event as the idempotency key using JMESPath expressions
* Set a time window in which records with the same payload should be considered duplicates
* Expires in-progress executions if the Lambda function times out halfway through

## Terminology

The property of idempotency means that an operation does not cause additional side effects if it is called more than once with the same input parameters.

**Idempotent operations will return the same result when they are called multiple times with the same parameters**. This makes idempotent operations safe to retry.

**Idempotency key** is a hash representation of either the entire event or a specific configured subset of the event, and invocation results are **JSON serialized** and stored in your persistence storage layer.

**Idempotency record** is the data representation of an idempotent request saved in your preferred  storage layer. We use it to coordinate whether a request is idempotent, whether it's still valid or expired based on timestamps, etc.

<center>
```mermaid
classDiagram
    direction LR
    class IdempotencyRecord {
        idempotency_key str
        status Status
        expiry_timestamp int
        in_progress_expiry_timestamp int
        response_data Json~str~
        payload_hash str
    }
    class Status {
        <<Enumeration>>
        INPROGRESS
        COMPLETE
        EXPIRED internal_only
    }
    IdempotencyRecord -- Status
```

<i>Idempotency record representation</i>
</center>

## Getting started

### IAM Permissions

Your Lambda function IAM Role must have `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem` and `dynamodb:DeleteItem` IAM permissions before using this feature.

???+ note
    If you're using our example [AWS Serverless Application Model (SAM)](#required-resources), [AWS Cloud Development Kit (CDK)](#required-resources), or [Terraform](#required-resources) it already adds the required permissions.

### Required resources

Before getting started, you need to create a persistent storage layer where the idempotency utility can store its state - your lambda functions will need read and write access to it.

As of now, Amazon DynamoDB is the only supported persistent storage layer, so you'll need to create a table first.

**Default table configuration**

If you're not [changing the default configuration for the DynamoDB persistence layer](#dynamodbpersistencelayer), this is the expected default configuration:

| Configuration      | Value        | Notes                                                                               |
| ------------------ | ------------ | ----------------------------------------------------------------------------------- |
| Partition key      | `id`         |
| TTL attribute name | `expiration` | This can only be configured after your table is created if you're using AWS Console |

???+ tip "Tip: You can share a single state table for all functions"
    You can reuse the same DynamoDB table to store idempotency state. We add `module_name` and [qualified name for classes and functions](https://peps.python.org/pep-3155/){target="_blank"} in addition to the idempotency key as a hash key.

=== "AWS Serverless Application Model (SAM) example"

    ```yaml hl_lines="6-14 24-31"
    --8<-- "examples/idempotency/templates/sam.yaml"
    ```
=== "AWS Cloud Development Kit (CDK)"

    ```python hl_lines="10 13 16 19-21"
    --8<-- "examples/idempotency/templates/cdk.py"
    ```

=== "Terraform"

    ```terraform hl_lines="14-26 64-70"
    --8<-- "examples/idempotency/templates/terraform.tf"
    ```

???+ warning "Warning: Large responses with DynamoDB persistence layer"
    When using this utility with DynamoDB, your function's responses must be [smaller than 400KB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Limits.html#limits-items){target="_blank"}.

    Larger items cannot be written to DynamoDB and will cause exceptions.

???+ info "Info: DynamoDB"
    Each function invocation will generally make 2 requests to DynamoDB. If the
    result returned by your Lambda is less than 1kb, you can expect 2 WCUs per invocation. For retried invocations, you will
    see 1WCU and 1RCU. Review the [DynamoDB pricing documentation](https://aws.amazon.com/dynamodb/pricing/){target="_blank"} to
    estimate the cost.

### Idempotent decorator

You can quickly start by initializing the `DynamoDBPersistenceLayer` class and using it with the `idempotent` decorator on your lambda handler.

???+ note
    In this example, the entire Lambda handler is treated as a single idempotent operation. If your Lambda handler can cause multiple side effects, or you're only interested in making a specific logic idempotent, use [`idempotent_function`](#idempotent_function-decorator) instead.

!!! tip "See [Choosing a payload subset for idempotency](#choosing-a-payload-subset-for-idempotency) for more elaborate use cases."

=== "Idempotent decorator"

    ```python hl_lines="4-7 10 24"
    --8<-- "examples/idempotency/src/getting_started_with_idempotency.py"
    ```

=== "Sample event"

    ```json
    --8<-- "examples/idempotency/src/getting_started_with_idempotency_payload.json"
    ```

After processing this request successfully, a second request containing the exact same payload above will now return the same response, ensuring our customer isn't charged twice.

!!! question "New to idempotency concept? Please review our [Terminology](#terminology) section if you haven't yet."

### Idempotent_function decorator

Similar to [idempotent decorator](#idempotent-decorator), you can use `idempotent_function` decorator for any synchronous Python function.

When using `idempotent_function`, you must tell us which keyword parameter in your function signature has the data we should use via **`data_keyword_argument`**.

!!! tip "We support JSON serializable data, [Python Dataclasses](https://docs.python.org/3.7/library/dataclasses.html){target="_blank"}, [Parser/Pydantic Models](parser.md){target="_blank"}, and our [Event Source Data Classes](./data_classes.md){target="_blank"}."

???+ warning "Limitation"
    Make sure to call your decorated function using keyword arguments.

=== "Using Dataclasses"

    ```python hl_lines="3-7 11 26 37"
    --8<-- "examples/idempotency/src/working_with_idempotent_function_dataclass.py"
    ```

=== "Using Pydantic"

    ```python hl_lines="1-5 10 23 34"
    --8<-- "examples/idempotency/src/working_with_idempotent_function_pydantic.py"
    ```

#### Batch integration

You can can easily integrate with [Batch utility](batch.md){target="_blank"} via context manager. This ensures that you process each record in an idempotent manner, and guard against a [Lambda timeout](#lambda-timeouts) idempotent situation.

???+ "Choosing an unique batch record attribute"
    In this example, we choose `messageId` as our idempotency key since we know it'll be unique.

    Depending on your use case, it might be more accurate [to choose another field](#choosing-a-payload-subset-for-idempotency) your producer intentionally set to define uniqueness.

=== "Integration with Batch Processor"

    ```python hl_lines="2 12 16 20 31 35 37"
    --8<-- "examples/idempotency/src/integrate_idempotency_with_batch_processor.py"
    ```

=== "Sample event"

    ```json hl_lines="4"
    --8<-- "examples/idempotency/src/integrate_idempotency_with_batch_processor_payload.json"
    ```

### Choosing a payload subset for idempotency

???+ tip "Tip: Dealing with always changing payloads"
    When dealing with a more elaborate payload, where parts of the payload always change, you should use **`event_key_jmespath`** parameter.

Use [`IdempotencyConfig`](#customizing-the-default-behavior) to instruct the idempotent decorator to only use a portion of your payload to verify whether a request is idempotent, and therefore it should not be retried.

> **Payment scenario**

In this example, we have a Lambda handler that creates a payment for a user subscribing to a product. We want to ensure that we don't accidentally charge our customer by subscribing them more than once.

Imagine the function executes successfully, but the client never receives the response due to a connection issue. It is safe to retry in this instance, as the idempotent decorator will return a previously saved response.

**What we want here** is to instruct Idempotency to use `user_id` and `product_id` fields from our incoming payload as our idempotency key.
If we were to treat the entire request as our idempotency key, a simple HTTP header change would cause our customer to be charged twice.

???+ tip "Deserializing JSON strings in payloads for increased accuracy."
    The payload extracted by the `event_key_jmespath` is treated as a string by default.
    This means there could be differences in whitespace even when the JSON payload itself is identical.

    To alter this behaviour, we can use the [JMESPath built-in function](jmespath_functions.md#powertools_json-function){target="_blank"} `powertools_json()` to treat the payload as a JSON object (dict) rather than a string.

=== "Payment function"

    ```python hl_lines="5-9 16 30"
    --8<-- "examples/idempotency/src/working_with_payload_subset.py"
    ```

=== "Sample event"

    ```json hl_lines="28"
    --8<-- "examples/idempotency/src/working_with_payload_subset_payload.json"
    ```

### Lambda timeouts

???+ note
    This is automatically done when you decorate your Lambda handler with [@idempotent decorator](#idempotent-decorator).

To prevent against extended failed retries when a [Lambda function times out](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-verify-invocation-timeouts/){target="_blank"},
Powertools for AWS Lambda (Python) calculates and includes the remaining invocation available time as part of the idempotency record.

???+ example
    If a second invocation happens **after** this timestamp, and the record is marked as `INPROGRESS`, we will execute the invocation again as if it was in the `EXPIRED` state (e.g, `expire_seconds` field elapsed).

    This means that if an invocation expired during execution, it will be quickly executed again on the next retry.

???+ important
    If you are only using the [@idempotent_function decorator](#idempotent_function-decorator) to guard isolated parts of your code,
    you must use `register_lambda_context` available in the [idempotency config object](#customizing-the-default-behavior) to benefit from this protection.

Here is an example on how you register the Lambda context in your handler:

=== "Registering the Lambda context"

    ```python hl_lines="11 20"
    --8<-- "examples/idempotency/src/working_with_lambda_timeout.py"
    ```

### Handling exceptions

If you are using the `idempotent` decorator on your Lambda handler, any unhandled exceptions that are raised during the code execution will cause **the record in the persistence layer to be deleted**.
This means that new invocations will execute your code again despite having the same payload. If you don't want the record to be deleted, you need to catch exceptions within the idempotent function and return a successful response.

<center>
```mermaid
sequenceDiagram
    participant Client
    participant Lambda
    participant Persistence Layer
    Client->>Lambda: Invoke (event)
    Lambda->>Persistence Layer: Get or set (id=event.search(payload))
    activate Persistence Layer
    Note right of Persistence Layer: Locked during this time. Prevents multiple<br/>Lambda invocations with the same<br/>payload running concurrently.
    Lambda--xLambda: Call handler (event).<br/>Raises exception
    Lambda->>Persistence Layer: Delete record (id=event.search(payload))
    deactivate Persistence Layer
    Lambda-->>Client: Return error response
```
<i>Idempotent sequence exception</i>
</center>

If you are using `idempotent_function`, any unhandled exceptions that are raised _inside_ the decorated function will cause the record in the persistence layer to be deleted, and allow the function to be executed again if retried.

If an Exception is raised _outside_ the scope of the decorated function and after your function has been called, the persistent record will not be affected. In this case, idempotency will be maintained for your decorated function. Example:

=== "Handling exceptions"

    ```python hl_lines="18-22 28 31"
    --8<-- "examples/idempotency/src/working_with_exceptions.py"
    ```

???+ warning
    **We will raise `IdempotencyPersistenceLayerError`** if any of the calls to the persistence layer fail unexpectedly.

    As this happens outside the scope of your decorated function, you are not able to catch it if you're using the `idempotent` decorator on your Lambda handler.

### Idempotency request flow

The following sequence diagrams explain how the Idempotency feature behaves under different scenarios.

#### Successful request

<center>
```mermaid
sequenceDiagram
    participant Client
    participant Lambda
    participant Persistence Layer
    alt initial request
        Client->>Lambda: Invoke (event)
        Lambda->>Persistence Layer: Get or set idempotency_key=hash(payload)
        activate Persistence Layer
        Note over Lambda,Persistence Layer: Set record status to INPROGRESS. <br> Prevents concurrent invocations <br> with the same payload
        Lambda-->>Lambda: Call your function
        Lambda->>Persistence Layer: Update record with result
        deactivate Persistence Layer
        Persistence Layer-->>Persistence Layer: Update record
        Note over Lambda,Persistence Layer: Set record status to COMPLETE. <br> New invocations with the same payload <br> now return the same result
        Lambda-->>Client: Response sent to client
    else retried request
        Client->>Lambda: Invoke (event)
        Lambda->>Persistence Layer: Get or set idempotency_key=hash(payload)
        activate Persistence Layer
        Persistence Layer-->>Lambda: Already exists in persistence layer.
        deactivate Persistence Layer
        Note over Lambda,Persistence Layer: Record status is COMPLETE and not expired
        Lambda-->>Client: Same response sent to client
    end
```
<i>Idempotent successful request</i>
</center>

#### Successful request with cache enabled

!!! note "[In-memory cache is disabled by default](#using-in-memory-cache)."

<center>
```mermaid
sequenceDiagram
    participant Client
    participant Lambda
    participant Persistence Layer
    alt initial request
      Client->>Lambda: Invoke (event)
      Lambda->>Persistence Layer: Get or set idempotency_key=hash(payload)
      activate Persistence Layer
      Note over Lambda,Persistence Layer: Set record status to INPROGRESS. <br> Prevents concurrent invocations <br> with the same payload
      Lambda-->>Lambda: Call your function
      Lambda->>Persistence Layer: Update record with result
      deactivate Persistence Layer
      Persistence Layer-->>Persistence Layer: Update record
      Note over Lambda,Persistence Layer: Set record status to COMPLETE. <br> New invocations with the same payload <br> now return the same result
      Lambda-->>Lambda: Save record and result in memory
      Lambda-->>Client: Response sent to client
    else retried request
      Client->>Lambda: Invoke (event)
      Lambda-->>Lambda: Get idempotency_key=hash(payload)
      Note over Lambda,Persistence Layer: Record status is COMPLETE and not expired
      Lambda-->>Client: Same response sent to client
    end
```
<i>Idempotent successful request cached</i>
</center>

#### Expired idempotency records

<center>
```mermaid
sequenceDiagram
    participant Client
    participant Lambda
    participant Persistence Layer
    alt initial request
        Client->>Lambda: Invoke (event)
        Lambda->>Persistence Layer: Get or set idempotency_key=hash(payload)
        activate Persistence Layer
        Note over Lambda,Persistence Layer: Set record status to INPROGRESS. <br> Prevents concurrent invocations <br> with the same payload
        Lambda-->>Lambda: Call your function
        Lambda->>Persistence Layer: Update record with result
        deactivate Persistence Layer
        Persistence Layer-->>Persistence Layer: Update record
        Note over Lambda,Persistence Layer: Set record status to COMPLETE. <br> New invocations with the same payload <br> now return the same result
        Lambda-->>Client: Response sent to client
    else retried request
        Client->>Lambda: Invoke (event)
        Lambda->>Persistence Layer: Get or set idempotency_key=hash(payload)
        activate Persistence Layer
        Persistence Layer-->>Lambda: Already exists in persistence layer.
        deactivate Persistence Layer
        Note over Lambda,Persistence Layer: Record status is COMPLETE but expired hours ago
        loop Repeat initial request process
            Note over Lambda,Persistence Layer: 1. Set record to INPROGRESS, <br> 2. Call your function, <br> 3. Set record to COMPLETE
        end
        Lambda-->>Client: Same response sent to client
    end
```
<i>Previous Idempotent request expired</i>
</center>

#### Concurrent identical in-flight requests

<center>
```mermaid
sequenceDiagram
    participant Client
    participant Lambda
    participant Persistence Layer
    Client->>Lambda: Invoke (event)
    Lambda->>Persistence Layer: Get or set idempotency_key=hash(payload)
    activate Persistence Layer
    Note over Lambda,Persistence Layer: Set record status to INPROGRESS. <br> Prevents concurrent invocations <br> with the same payload
      par Second request
          Client->>Lambda: Invoke (event)
          Lambda->>Persistence Layer: Get or set idempotency_key=hash(payload)
          Lambda--xLambda: IdempotencyAlreadyInProgressError
          Lambda->>Client: Error sent to client if unhandled
      end
    Lambda-->>Lambda: Call your function
    Lambda->>Persistence Layer: Update record with result
    deactivate Persistence Layer
    Persistence Layer-->>Persistence Layer: Update record
    Note over Lambda,Persistence Layer: Set record status to COMPLETE. <br> New invocations with the same payload <br> now return the same result
    Lambda-->>Client: Response sent to client
```
<i>Concurrent identical in-flight requests</i>
</center>

#### Lambda request timeout

<center>
```mermaid
sequenceDiagram
    participant Client
    participant Lambda
    participant Persistence Layer
    alt initial request
        Client->>Lambda: Invoke (event)
        Lambda->>Persistence Layer: Get or set idempotency_key=hash(payload)
        activate Persistence Layer
        Note over Lambda,Persistence Layer: Set record status to INPROGRESS. <br> Prevents concurrent invocations <br> with the same payload
        Lambda-->>Lambda: Call your function
        Note right of Lambda: Time out
        Lambda--xLambda: Time out error
        Lambda-->>Client: Return error response
        deactivate Persistence Layer
    else retry after Lambda timeout elapses
        Client->>Lambda: Invoke (event)
        Lambda->>Persistence Layer: Get or set idempotency_key=hash(payload)
        activate Persistence Layer
        Note over Lambda,Persistence Layer: Set record status to INPROGRESS. <br> Reset in_progress_expiry attribute
        Lambda-->>Lambda: Call your function
        Lambda->>Persistence Layer: Update record with result
        deactivate Persistence Layer
        Persistence Layer-->>Persistence Layer: Update record
        Lambda-->>Client: Response sent to client
    end
```
<i>Idempotent request during and after Lambda timeouts</i>
</center>

#### Optional idempotency key

<center>
```mermaid
sequenceDiagram
    participant Client
    participant Lambda
    participant Persistence Layer
    alt request with idempotency key
        Client->>Lambda: Invoke (event)
        Lambda->>Persistence Layer: Get or set idempotency_key=hash(payload)
        activate Persistence Layer
        Note over Lambda,Persistence Layer: Set record status to INPROGRESS. <br> Prevents concurrent invocations <br> with the same payload
        Lambda-->>Lambda: Call your function
        Lambda->>Persistence Layer: Update record with result
        deactivate Persistence Layer
        Persistence Layer-->>Persistence Layer: Update record
        Note over Lambda,Persistence Layer: Set record status to COMPLETE. <br> New invocations with the same payload <br> now return the same result
        Lambda-->>Client: Response sent to client
    else request(s) without idempotency key
        Client->>Lambda: Invoke (event)
        Note over Lambda: Idempotency key is missing
        Note over Persistence Layer: Skips any operation to fetch, update, and delete
        Lambda-->>Lambda: Call your function
        Lambda-->>Client: Response sent to client
    end
```
<i>Optional idempotency key</i>
</center>

## Advanced

### Persistence layers

#### DynamoDBPersistenceLayer

This persistence layer is built-in, and you can either use an existing DynamoDB table or create a new one dedicated for idempotency state (recommended).

=== "Customizing DynamoDBPersistenceLayer to suit your table structure"

    ```python hl_lines="7-15"
    --8<-- "examples/idempotency/src/customize_persistence_layer.py"
    ```

When using DynamoDB as a persistence layer, you can alter the attribute names by passing these parameters when initializing the persistence layer:

| Parameter                   | Required           | Default                              | Description                                                                                              |
| --------------------------- | ------------------ | ------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| **table_name**              | :heavy_check_mark: |                                      | Table name to store state                                                                                |
| **key_attr**                |                    | `id`                                 | Partition key of the table. Hashed representation of the payload (unless **sort_key_attr** is specified) |
| **expiry_attr**             |                    | `expiration`                         | Unix timestamp of when record expires                                                                    |
| **in_progress_expiry_attr** |                    | `in_progress_expiration`             | Unix timestamp of when record expires while in progress (in case of the invocation times out)            |
| **status_attr**             |                    | `status`                             | Stores status of the lambda execution during and after invocation                                        |
| **data_attr**               |                    | `data`                               | Stores results of successfully executed Lambda handlers                                                  |
| **validation_key_attr**     |                    | `validation`                         | Hashed representation of the parts of the event used for validation                                      |
| **sort_key_attr**           |                    |                                      | Sort key of the table (if table is configured with a sort key).                                          |
| **static_pk_value**         |                    | `idempotency#{LAMBDA_FUNCTION_NAME}` | Static value to use as the partition key. Only used when **sort_key_attr** is set.                       |

### Customizing the default behavior

Idempotent decorator can be further configured with **`IdempotencyConfig`** as seen in the previous example. These are the available options for further configuration

| Parameter                       | Default | Description                                                                                                                                                |
| ------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **event_key_jmespath**          | `""`    | JMESPath expression to extract the idempotency key from the event record using [built-in functions](/utilities/jmespath_functions){target="_blank"}        |
| **payload_validation_jmespath** | `""`    | JMESPath expression to validate whether certain parameters have changed in the event while the event payload                                               |
| **raise_on_no_idempotency_key** | `False` | Raise exception if no idempotency key was found in the request                                                                                             |
| **expires_after_seconds**       | 3600    | The number of seconds to wait before a record is expired                                                                                                   |
| **use_local_cache**             | `False` | Whether to locally cache idempotency results                                                                                                               |
| **local_cache_max_items**       | 256     | Max number of items to store in local cache                                                                                                                |
| **hash_function**               | `md5`   | Function to use for calculating hashes, as provided by [hashlib](https://docs.python.org/3/library/hashlib.html){target="_blank"} in the standard library. |

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

=== "Caching idempotent transactions in-memory to prevent multiple calls to storage"

    ```python hl_lines="11"
    --8<-- "examples/idempotency/src/working_with_local_cache.py"
    ```

=== "Sample event"

    ```json
    --8<-- "examples/idempotency/src/working_with_local_cache_payload.json"
    ```

When enabled, the default is to cache a maximum of 256 records in each Lambda execution environment - You can change it with the **`local_cache_max_items`** parameter.

### Expiring idempotency records

!!! note "By default, we expire idempotency records after **an hour** (3600 seconds)."

In most cases, it is not desirable to store the idempotency records forever. Rather, you want to guarantee that the same payload won't be executed within a period of time.

You can change this window with the **`expires_after_seconds`** parameter:

=== "Adjusting idempotency record expiration"

    ```python hl_lines="11"
    --8<-- "examples/idempotency/src/working_with_record_expiration.py"
    ```

=== "Sample event"

    ```json
    --8<-- "examples/idempotency/src/working_with_record_expiration_payload.json"
    ```

This will mark any records older than 5 minutes as expired, and [your function will be executed as normal if it is invoked with a matching payload](#expired-idempotency-records).

???+ important "Idempotency record expiration vs DynamoDB time-to-live (TTL)"
    [DynamoDB TTL is a feature](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/howitworks-ttl.html){target="_blank"} to remove items after a certain period of time, it may occur within 48 hours of expiration.

    We don't rely on DynamoDB or any persistence storage layer to determine whether a record is expired to avoid eventual inconsistency states.

    Instead, Idempotency records saved in the storage layer contain timestamps that can be verified upon retrieval and double checked within Idempotency feature.

    **Why?**

    A record might still be valid (`COMPLETE`) when we retrieved, but in some rare cases it might expire a second later. A record could also be [cached in memory](#using-in-memory-cache). You might also want to have idempotent transactions that should expire in seconds.

### Payload validation

???+ question "Question: What if your function is invoked with the same payload except some outer parameters have changed?"
    Example: A payment transaction for a given productID was requested twice for the same customer, **however the amount to be paid has changed in the second transaction**.

By default, we will return the same result as it returned before, however in this instance it may be misleading; we provide a fail fast payload validation to address this edge case.

With **`payload_validation_jmespath`**, you can provide an additional JMESPath expression to specify which part of the event body should be validated against previous idempotent invocations

=== "Payload validation"

    ```python hl_lines="12 20 28"
    --8<-- "examples/idempotency/src/working_with_validation_payload.py"
    ```

=== "Sample event 1"

    ```json hl_lines="2 5"
    --8<-- "examples/idempotency/src/working_with_validation_payload_payload1.json"
    ```

=== "Sample event 2"

    ```json hl_lines="2 5"
    --8<-- "examples/idempotency/src/working_with_validation_payload_payload2.json"
    ```

In this example, the **`user_id`** and **`product_id`** keys are used as the payload to generate the idempotency key, as per **`event_key_jmespath`** parameter.

???+ note
    If we try to send the same request but with a different amount, we will raise **`IdempotencyValidationError`**.

Without payload validation, we would have returned the same result as we did for the initial request. Since we're also returning an amount in the response, this could be quite confusing for the client.

By using **`payload_validation_jmespath="amount"`**, we prevent this potentially confusing behavior and instead raise an Exception.

### Making idempotency key required

If you want to enforce that an idempotency key is required, you can set **`raise_on_no_idempotency_key`** to `True`.

This means that we will raise **`IdempotencyKeyError`** if the evaluation of **`event_key_jmespath`** is `None`.

???+ warning
    To prevent errors, transactions will not be treated as idempotent if **`raise_on_no_idempotency_key`** is set to `False` and the evaluation of **`event_key_jmespath`** is `None`. Therefore, no data will be fetched, stored, or deleted in the idempotency storage layer.

=== "Idempotency key required"

    ```python hl_lines="11"
    --8<-- "examples/idempotency/src/working_with_idempotency_key_required.py"
    ```

=== "Success Event"

    ```json hl_lines="3 6"
    --8<-- "examples/idempotency/src/working_with_idempotency_key_required_payload_success.json"
    ```

=== "Failure Event"

    ```json hl_lines="3 5"
    --8<-- "examples/idempotency/src/working_with_idempotency_key_required_payload_error.json"
    ```

### Customizing boto configuration

The **`boto_config`** and **`boto3_session`** parameters enable you to pass in a custom [botocore config object](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html){target="_blank"} or a custom [boto3 session](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html){target="_blank"} when constructing the persistence store.

=== "Custom session"

    ```python hl_lines="1 11 13"
    --8<-- "examples/idempotency/src/working_with_custom_session.py"
    ```

=== "Custom config"

    ```python hl_lines="1 11 13"
    --8<-- "examples/idempotency/src/working_with_custom_config.py"
    ```

=== "Sample Event"

    ```json
    --8<-- "examples/idempotency/src/working_with_custom_config_payload.json"
    ```

### Using a DynamoDB table with a composite primary key

When using a composite primary key table (hash+range key), use `sort_key_attr` parameter when initializing your persistence layer.

With this setting, we will save the idempotency key in the sort key instead of the primary key. By default, the primary key will now be set to `idempotency#{LAMBDA_FUNCTION_NAME}`.

You can optionally set a static value for the partition key using the `static_pk_value` parameter.

=== "Reusing a DynamoDB table that uses a composite primary key"

    ```python hl_lines="7"
    --8<-- "examples/idempotency/src/working_with_composite_key.py"
    ```

=== "Sample Event"

    ```json
    --8<-- "examples/idempotency/src/working_with_composite_key_payload.json"
    ```

The example function above would cause data to be stored in DynamoDB like this:

| id                           | sort_key                         | expiration | status      | data                                      |
| ---------------------------- | -------------------------------- | ---------- | ----------- | ----------------------------------------- |
| idempotency#MyLambdaFunction | 1e956ef7da78d0cb890be999aecc0c9e | 1636549553 | COMPLETED   | {"user_id": 12391, "message": "success"}  |
| idempotency#MyLambdaFunction | 2b2cdb5f86361e97b4383087c1ffdf27 | 1636549571 | COMPLETED   | {"user_id": 527212, "message": "success"} |
| idempotency#MyLambdaFunction | f091d2527ad1c78f05d54cc3f363be80 | 1636549585 | IN_PROGRESS |                                           |

### Bring your own persistent store

This utility provides an abstract base class (ABC), so that you can implement your choice of persistent storage layer.

You can create your own persistent store from scratch by inheriting the `BasePersistenceLayer` class, and implementing `_get_record()`, `_put_record()`, `_update_record()` and `_delete_record()`.

* **`_get_record()`** – Retrieves an item from the persistence store using an idempotency key and returns it as a `DataRecord` instance.
* **`_put_record()`** – Adds a `DataRecord` to the persistence store if it doesn't already exist with that key. Raises an `ItemAlreadyExists` exception if a non-expired entry already exists.
* **`_update_record()`** – Updates an item in the persistence store.
* **`_delete_record()`** – Removes an item from the persistence store.

=== "Bring your own persistent store"

    ```python hl_lines="8 18 65 74 96 124"
    --8<-- "examples/idempotency/src/bring_your_own_persistent_store.py"
    ```

???+ danger
    Pay attention to the documentation for each - you may need to perform additional checks inside these methods to ensure the idempotency guarantees remain intact.

    For example, the `_put_record` method needs to raise an exception if a non-expired record already exists in the data store with a matching key.

## Compatibility with other utilities

### Batch

See [Batch integration](#batch-integration) above.

### Validation utility

The idempotency utility can be used with the `validator` decorator. Ensure that idempotency is the innermost decorator.

???+ warning
    If you use an envelope with the validator, the event received by the idempotency utility will be the unwrapped
    event - not the "raw" event Lambda was invoked with.

	Make sure to account for this behaviour, if you set the `event_key_jmespath`.

=== "Using Idempotency with JSONSchema Validation utility"

    ```python hl_lines="13"
    --8<-- "examples/idempotency/src/integrate_idempotency_with_validator.py"
    ```

=== "Sample Event"

    ```json hl_lines="60"
    --8<-- "examples/idempotency/src/integrate_idempotency_with_validator_payload.json"
    ```

???+ tip "Tip: JMESPath Powertools for AWS Lambda (Python) functions are also available"
    Built-in functions known in the validation utility like `powertools_json`, `powertools_base64`, `powertools_base64_gzip` are also available to use in this utility.

## Testing your code

The idempotency utility provides several routes to test your code.

### Disabling the idempotency utility

When testing your code, you may wish to disable the idempotency logic altogether and focus on testing your business logic. To do this, you can set the environment variable `POWERTOOLS_IDEMPOTENCY_DISABLED`
with a truthy value. If you prefer setting this for specific tests, and are using Pytest, you can use [monkeypatch](https://docs.pytest.org/en/latest/monkeypatch.html){target="_blank"} fixture:

=== "test_disabling_idempotency_utility.py"

    ```python hl_lines="3 4 23 24"
    --8<-- "examples/idempotency/tests/test_disabling_idempotency_utility.py"
    ```

=== "app_test_disabling_idempotency_utility.py"

    ```python hl_lines="10"
    --8<-- "examples/idempotency/tests/app_test_disabling_idempotency_utility.py"
    ```

### Testing with DynamoDB Local

To test with [DynamoDB Local](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html){target="_blank"}, you can replace the `DynamoDB client` used by the persistence layer with one you create inside your tests. This allows you to set the endpoint_url.

=== "test_with_dynamodb_local.py"

    ```python hl_lines="3-5 25 26"
    --8<-- "examples/idempotency/tests/test_with_dynamodb_local.py"
    ```

=== "app_test_dynamodb_local.py"

    ```python hl_lines="10"
    --8<-- "examples/idempotency/tests/app_test_dynamodb_local.py"
    ```

### How do I mock all DynamoDB I/O operations

The idempotency utility lazily creates the dynamodb [Table](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#table){target="_blank"} which it uses to access DynamoDB.
This means it is possible to pass a mocked Table resource, or stub various methods.

=== "test_with_io_operations.py"

    ```python hl_lines="4 5 24 25 27"
    --8<-- "examples/idempotency/tests/test_with_io_operations.py"
    ```

=== "app_test_io_operations.py"

    ```python hl_lines="10"
    --8<-- "examples/idempotency/tests/app_test_io_operations.py"
    ```

## Extra resources

If you're interested in a deep dive on how Amazon uses idempotency when building our APIs, check out
[this article](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/){target="_blank"}.
