---
title: Idempotency
description: Utility
---

This utility provides a simple solution to convert your Lambda functions into idempotent operations which are safe to
retry.

## Terminology

The property of idempotency means that an operation does not cause additional side effects if it is called more than
once with the same input parameters. Idempotent operations will return the same result when they are called multiple
times with the same parameters. This makes idempotent operations safe to retry.


## Key features

* Prevent Lambda handler code executing more than once on the same event payload during a time window
* Ensure Lambda handler returns the same result when called with the same payload
* Select a subset of the event as the idempotency key using JMESpath expressions
* Set a time window in which records with the same payload should be considered duplicates

## Getting started

### Required resources

Before getting started, you need to create a DynamoDB table to store state used by the idempotency utility. Your lambda
functions will need read and write access to this table.

> Example using AWS Serverless Application Model (SAM)

=== "template.yml"
```yaml
Resources:
  HelloWorldFunction:
  Type: AWS::Serverless::Function
  Properties:
    Runtime: python3.8
    ...
    Policies:
      - DynamoDBCrudPolicy:
          TableName: !Ref IdempotencyTable
  IdempotencyTable:
    Type: AWS::DynamoDB::Table
    Properties:
      AttributeDefinitions:
        -   AttributeName: id
            AttributeType: S
      BillingMode: PAY_PER_REQUEST
      KeySchema:
        -   AttributeName: id
            KeyType: HASH
      TableName: "IdempotencyTable"
      TimeToLiveSpecification:
        AttributeName: expiration
        Enabled: true
```

!!! note
    When using this utility, each function invocation will generally make 2 requests to DynamoDB. If the result
    returned by your Lambda is less than 1kb, you can expect 2 WCUs per invocation. For retried invocations, you will
    see 1WCU and 1RCU. Review the [DynamoDB pricing documentation](https://aws.amazon.com/dynamodb/pricing/) to
    estimate the cost.


### Lambda handler

You can quickly start by initializing the `DynamoDBPersistenceLayer` class outside the Lambda handler, and using it
with the `idempotent` decorator on your lambda handler. The only required parameter is `table_name`, but you likely
want to specify `event_key_jmespath` as well.

`event_key_jmespath`: A JMESpath expression which will be used to extract the payload from the event your Lambda hander
is called with. This payload will be used as the key to decide if future invocations are duplicates. If you don't pass
this parameter, the entire event will be used as the key.

=== "app.py"

    ```python hl_lines="2 6-9 11"
        import json
        from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, idempotent

        # Treat everything under the "body" key in
        # the event json object as our payload
        persistence_layer = DynamoDBPersistenceLayer(
            event_key_jmespath="body",
            table_name="IdempotencyTable"
            )

        @idempotent(persistence_store=persistence_layer)
        def handler(event, context):
            body = json.loads(event['body'])
            payment = create_subscription_payment(
                user=body['user'],
                product=body['product_id']
                )
            ...
            return {"message": "success", "statusCode": 200, "payment_id": payment.id}
    ```
=== "Example event"

    ```json
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
      "body":"{\"username\":\"xyz\",\"product_id\":\"123456789\"}",
      "isBase64Encoded":false
    }
    ```

In this example, we have a Lambda handler that creates a payment for a user subscribing to a product. We want to ensure
that we don't accidentally charge our customer by subscribing them more than once. Imagine the function executes
successfully, but the client never receives the response. When we're using the idempotent decorator, we can safely
retry. This sequence diagram shows an example flow of what happens in this case:

![Idempotent sequence](../media/idempotent_sequence.png)


The client was successful in receiving the result after the retry. Since the Lambda handler was only executed once, our
customer hasn't been charged twice.

!!! note
    Bear in mind that the entire Lambda handler is treated as a single idempotent operation. If your Lambda handler can
    cause multiple side effects, consider splitting it into separate functions.

### Handling exceptions

If your Lambda handler raises an unhandled exception, the record in the persistence layer will be deleted. This means
that if the client retries, your Lambda handler will be free to execute again. If you don't want the record to be
deleted, you need to catch Exceptions within the handler and return a successful response.


![Idempotent sequence exception](../media/idempotent_sequence_exception.png)

!!! warning
    If any of the calls to the persistence layer unexpectedly fail, `IdempotencyPersistenceLayerError` will be raised.
    As this happens outside the scope of your Lambda handler, you are not able to catch it.

### Setting a time window
In most cases, it is not desirable to store the idempotency records forever. Rather, you want to guarantee that the
same payload won't be executed within a period of time. By default, the period is set to 1 hour (3600 seconds). You can
change this window with the `expires_after_seconds` parameter:

```python hl_lines="4"
DynamoDBPersistenceLayer(
    event_key_jmespath="body",
    table_name="IdempotencyTable",
    expires_after_seconds=5*60  # 5 minutes
    )

```
This will mark any records older than 5 minutes expired, and the lambda handler will be executed as normal if it is
invoked with a matching payload. If you have set the TTL field in DynamoDB like in the SAM example above, the record
will be automatically deleted from the table after a period of itme.


### Using local cache
To reduce the number of lookups to the persistence storage layer, you can enable in memory caching with the
`use_local_cache` parameter, which is disabled by default. This cache is local to each Lambda execution environment.
This means it will be effective in cases where your function's concurrency is low in comparison to the number of
"retry" invocations with the same payload. When enabled, the default is to cache a maxmum of 256 records in each Lambda
execution environment. You can change this with the `local_cache_max_items` parameter.

```python hl_lines="4 5"
DynamoDBPersistenceLayer(
    event_key_jmespath="body",
    table_name="IdempotencyTable",
    use_local_cache=True,
    local_cache_max_items=1000
    )
```


## Advanced

### Payload validation
What happens if lambda is invoked with a payload that it has seen before, but some parameters which are not part of the
payload have changed? By default, lambda will return the same result as it returned before, which may be misleading.
Payload validation provides a solution to that. You can provide another JMESpath expression to the persistence store
with the `payload_validation_jmespath` to specify which part of the event body should be validated against previous
idempotent invocations.

=== "app.py"
    ```python hl_lines="6"
    from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, idempotent

        persistence_layer = DynamoDBPersistenceLayer(
            event_key_jmespath="[userDetail, productId]",
            table_name="IdempotencyTable",)
            payload_validation_jmespath="amount"
            )

        @idempotent(persistence_store=persistence_layer)
        def handler(event, context):
            # Creating a subscription payment is a side
            # effect of calling this function!
            payment = create_subscription_payment(
            user=event['userDetail']['username'],
            product=event['product_id'],
            amount=event['amount']
            )
            ...
            return {"message": "success", "statusCode": 200,
                    "payment_id": payment.id, "amount": payment.amount}
    ```
=== "Event"
    ```json
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

In this example, the "userDetail" and "productId" keys are used as the payload to generate the idempotency key. If
we try to send the same request but with a different amount, Lambda will raise `IdempotencyValidationError`. Without
payload validation, we would have returned the same result as we did for the initial request. Since we're also
returning an amount in the response, this could be quite confusing for the client. By using payload validation on the
amount field, we prevent this potentially confusing behaviour and instead raise an Exception.

### Changing dynamoDB attribute names
If you want to use an existing DynamoDB table, or wish to change the name of the attributes used to store items in the
table, you can do so when you construct the `DynamoDBPersistenceLayer` instance.


Parameter           | Default value  | Description
------------------- |--------------- | ------------
key_attr            | "id"           | Primary key of the table. Hashed representation of the payload
expiry_attr         | "expiration"   | Unix timestamp of when record expires
status_attr         | "status"       | Stores status of the lambda execution during and after invocation
data_attr           | "data"         | Stores results of successfully executed Lambda handlers
validation_key_attr | "validation"   | Hashed representation of the parts of the event used for validation

This example demonstrates changing the attribute names to custom values:

=== "app.py"
    ```python hl_lines="5-10"
    persistence_layer = DynamoDBPersistenceLayer(
        event_key_jmespath="[userDetail, productId]",
        table_name="IdempotencyTable",)
        key_attr="idempotency_key",
        expiry_attr="expires_at",
        status_attr="current_status",
        data_attr="result_data",
        validation_key_attr="validation_key"
        )
    ```

### Customizing boto configuration
You can provide custom boto configuration or event bring your own boto3 session if required by using the `boto_config`
or `boto3_session` parameters when constructing the persistence store.

=== "Custom session"
    ```python hl_lines="1 4 8"
       import boto3
       from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, idempotent

       boto3_session = boto3.session.Session()
       persistence_layer = DynamoDBPersistenceLayer(
            event_key_jmespath="body",
            table_name="IdempotencyTable",
            boto3_session=boto3_session
            )

       @idempotent(persistence_store=persistence_layer)
       def handler(event, context):
           ...
    ```
=== "Custom config"
    ```python hl_lines="1 4 8"
       from botocore.config import Config
       from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, idempotent

       boto_config = Config()
       persistence_layer = DynamoDBPersistenceLayer(
           event_key_jmespath="body",
           table_name="IdempotencyTable",
           boto_config=boto_config
           )

       @idempotent(persistence_store=persistence_layer)
       def handler(event, context):
           ...
    ```

### Bring your own persistent store

The utility provides an abstract base class which can be used to implement your choice of persistent storage layers.
You can inherit from the `BasePersistenceLayer` class and implement the abstract methods `_get_record`, `_put_record`,
`_update_record` and `_delete_record`. Pay attention to the documentation for each - you may need to perform additional
checks inside these methods to ensure the idempotency guarantees remain intact. For example, the `_put_record` method
needs to raise an exception if a non-expired record already exists in the data store with a matching key.

## Extra resources
If you're interested in a deep dive on how Amazon uses idempotency when building our APIs, check out
[this article](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).
