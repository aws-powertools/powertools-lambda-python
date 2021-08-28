---
title: JMESPath Functions
description: Utility
---

You might have events or responses that contain non-encoded JSON, where you need to decode so that you can access portions of the object or ensure the Powertools utility recieves a JSON object

## Built-in JMESPath functions
You can use our built-in JMESPath functions within your expressions to do exactly that to decode JSON Strings, base64, and uncompress gzip data.

!!! info
    We use these for built-in envelopes to easily decode and unwrap events from sources like API Gateway, Kinesis, CloudWatch Logs, etc.

#### powertools_json function

Use `powertools_json` function to decode any JSON String anywhere a JMESPath expression is allowed.

> **Validation scenario**

This sample will decode the value within the `data` key into a valid JSON before we can validate it.

=== "powertools_json_jmespath_function.py"

    ```python hl_lines="9"
    from aws_lambda_powertools.utilities.validation import validate

    import schemas

    sample_event = {
        'data': '{"payload": {"message": "hello hello", "username": "blah blah"}}'
    }

    validate(event=sample_event, schema=schemas.INPUT, envelope="powertools_json(data)")
    ```

=== "schemas.py"

    ```python hl_lines="7 14 16 23 39 45 47 52"
    --8<-- "docs/shared/validation_basic_jsonschema.py"
    ```

> **Idempotency scenario**

This sample will decode the value within the `body` key of an API Gateway event into a valid JSON object to ensure the Idempotency utility processes a JSON object instead of a string.

=== "powertools_json_jmespath_function.py"

    ```python hl_lines="8"
    import json
    from aws_lambda_powertools.utilities.idempotency import (
        IdempotencyConfig, DynamoDBPersistenceLayer, idempotent
    )

    persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")

    config = IdempotencyConfig(event_key_jmespath="powertools_json(body)")
    @idempotent(config=config, persistence_store=persistence_layer)
    def handler(event:APIGatewayProxyEvent, context):
        body = json.loads(event['body'])
        payment = create_subscription_payment(
            user=body['user'],
            product=body['product_id']
        )
        ...
        return {
            "payment_id": payment.id,
            "message": "success",
            "statusCode": 200
        }
    ```

#### powertools_base64 function

Use `powertools_base64` function to decode any base64 data.

This sample will decode the base64 value within the `data` key, and decode the JSON string into a valid JSON before we can validate it.

=== "powertools_json_jmespath_function.py"

    ```python hl_lines="12"
    from aws_lambda_powertools.utilities.validation import validate

    import schemas

    sample_event = {
        "data": "eyJtZXNzYWdlIjogImhlbGxvIGhlbGxvIiwgInVzZXJuYW1lIjogImJsYWggYmxhaCJ9="
    }

    validate(
          event=sample_event,
          schema=schemas.INPUT,
          envelope="powertools_json(powertools_base64(data))"
    )
    ```

=== "schemas.py"

    ```python hl_lines="7 14 16 23 39 45 47 52"
    --8<-- "docs/shared/validation_basic_jsonschema.py"
    ```

#### powertools_base64_gzip function

Use `powertools_base64_gzip` function to decompress and decode base64 data.

This sample will decompress and decode base64 data, then use JMESPath pipeline expression to pass the result for decoding its JSON string.

=== "powertools_json_jmespath_function.py"

    ```python hl_lines="12"
    from aws_lambda_powertools.utilities.validation import validate

    import schemas

    sample_event = {
        "data": "H4sIACZAXl8C/52PzUrEMBhFX2UILpX8tPbHXWHqIOiq3Q1F0ubrWEiakqTWofTdTYYB0YWL2d5zvnuTFellBIOedoiyKH5M0iwnlKH7HZL6dDB6ngLDfLFYctUKjie9gHFaS/sAX1xNEq525QxwFXRGGMEkx4Th491rUZdV3YiIZ6Ljfd+lfSyAtZloacQgAkqSJCGhxM6t7cwwuUGPz4N0YKyvO6I9WDeMPMSo8Z4Ca/kJ6vMEYW5f1MX7W1lVxaG8vqX8hNFdjlc0iCBBSF4ERT/3Pl7RbMGMXF2KZMh/C+gDpNS7RRsp0OaRGzx0/t8e0jgmcczyLCWEePhni/23JWalzjdu0a3ZvgEaNLXeugEAAA=="
    }

    validate(
        event=sample_event,
        schema=schemas.INPUT,
        envelope="powertools_base64_gzip(data) | powertools_json(@)"
    )
    ```

=== "schemas.py"

    ```python hl_lines="7 14 16 23 39 45 47 52"
    --8<-- "docs/shared/validation_basic_jsonschema.py"
    ```

### Bring your own JMESPath function

!!! warning
    This should only be used for advanced use cases where you have special formats not covered by the built-in functions.

    This will **replace all provided built-in functions such as `powertools_json`, so you will no longer be able to use them**.

For special binary formats that you want to decode before applying JSON Schema validation, you can bring your own [JMESPath function](https://github.com/jmespath/jmespath.py#custom-functions){target="_blank"} and any additional option via `jmespath_options` param.

=== "custom_jmespath_function.py"

    ```python hl_lines="2 6-10 14"
    from aws_lambda_powertools.utilities.validation import validator
    from jmespath import functions

    import schemas

    class CustomFunctions(functions.Functions):

        @functions.signature({'types': ['string']})
        def _func_special_decoder(self, s):
            return my_custom_decoder_logic(s)

    custom_jmespath_options = {"custom_functions": CustomFunctions()}

    @validator(schema=schemas.INPUT, jmespath_options=**custom_jmespath_options)
    def handler(event, context):
        return event
    ```

=== "schemas.py"

    ```python hl_lines="7 14 16 23 39 45 47 52"
    --8<-- "docs/shared/validation_basic_jsonschema.py"
    ```
