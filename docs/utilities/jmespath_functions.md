---
title: JMESPath Functions
description: Utility
---

???+ tip
    JMESPath is a query language for JSON used by AWS CLI, AWS Python SDK, and AWS Lambda Powertools for Python.

Built-in [JMESPath](https://jmespath.org/){target="_blank"} Functions to easily deserialize common encoded JSON payloads in Lambda functions.

## Key features

* Deserialize JSON from JSON strings, base64, and compressed data
* Use JMESPath to extract and combine data recursively

## Getting started

You might have events that contains encoded JSON payloads as string, base64, or even in compressed format. It is a common use case to decode and extract them partially or fully as part of your Lambda function invocation.

Lambda Powertools also have utilities like [validation](validation.md), [idempotency](idempotency.md), or [feature flags](feature_flags.md) where you might need to extract a portion of your data before using them.

???+ info
    **Envelope** is the terminology we use for the JMESPath expression to extract your JSON object from your data input.

### Extracting data

You can use the `extract_data_from_envelope` function along with any [JMESPath expression](https://jmespath.org/tutorial.html){target="_blank"}.

=== "app.py"

	```python hl_lines="1 6"
    --8<-- "docs/examples/utilities/jmespath_functions/extract_data_jmespath.py"
	```

=== "event.json"

    ```json
    {
        "body": "{\"customerId\":\"dd4649e6-2484-4993-acb8-0f9123103394\"}"
    }
    ```

### Built-in envelopes

We provide built-in envelopes for popular JMESPath expressions used when looking to decode/deserialize JSON objects within AWS Lambda Event Sources.

=== "app.py"

	```python hl_lines="1 6"
    --8<-- "docs/examples/utilities/jmespath_functions/extract_data_built_in_jmespath.py"
	```

=== "event.json"

    ```json hl_lines="6"
    {
        "Records": [
            {
                "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
                "receiptHandle": "MessageReceiptHandle",
                "body": "{\"customerId\":\"dd4649e6-2484-4993-acb8-0f9123103394\",\"booking\":{\"id\":\"5b2c4803-330b-42b7-811a-c68689425de1\",\"reference\":\"ySz7oA\",\"outboundFlightId\":\"20c0d2f2-56a3-4068-bf20-ff7703db552d\"},\"payment\":{\"receipt\":\"https:\/\/pay.stripe.com\/receipts\/acct_1Dvn7pF4aIiftV70\/ch_3JTC14F4aIiftV700iFq2CHB\/rcpt_K7QsrFln9FgFnzUuBIiNdkkRYGxUL0X\",\"amount\":100}}",
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1523232000000",
                    "SenderId": "123456789012",
                    "ApproximateFirstReceiveTimestamp": "1523232000001"
                },
                "messageAttributes": {},
                "md5OfBody": "7b270e59b47ff90a553787216d55d91d",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
                "awsRegion": "us-east-1"
            }
        ]
    }
    ```

These are all built-in envelopes you can use along with their expression as a reference:

Envelope | JMESPath expression
------------------------------------------------- | ---------------------------------------------------------------------------------
**`API_GATEWAY_REST`** | `powertools_json(body)`
**`API_GATEWAY_HTTP`** | `API_GATEWAY_REST`
**`SQS`** | `Records[*].powertools_json(body)`
**`SNS`** | `Records[0].Sns.Message | powertools_json(@)`
**`EVENTBRIDGE`** | `detail`
**`CLOUDWATCH_EVENTS_SCHEDULED`** | `EVENTBRIDGE`
**`KINESIS_DATA_STREAM`** | `Records[*].kinesis.powertools_json(powertools_base64(data))`
**`CLOUDWATCH_LOGS`** | `awslogs.powertools_base64_gzip(data) | powertools_json(@).logEvents[*]`

## Advanced

### Built-in JMESPath functions

You can use our built-in JMESPath functions within your expressions to do exactly that to decode JSON Strings, base64, and uncompress gzip data.

???+ info
    We use these for built-in envelopes to easily decode and unwrap events from sources like API Gateway, Kinesis, CloudWatch Logs, etc.

#### powertools_json function

Use `powertools_json` function to decode any JSON String anywhere a JMESPath expression is allowed.

> **Validation scenario**

This sample will decode the value within the `data` key into a valid JSON before we can validate it.

=== "powertools_json_jmespath_function.py"

    ```python hl_lines="9"
    --8<-- "docs/examples/utilities/jmespath_functions/powertools_json_jmespath_function.py"
    ```

=== "schemas.py"

    ```python hl_lines="8 10 17 34 36 41"
    --8<-- "docs/shared/validation_basic_jsonschema.py"
    ```

> **Idempotency scenario**

This sample will decode the value within the `body` key of an API Gateway event into a valid JSON object to ensure the Idempotency utility processes a JSON object instead of a string.

```python hl_lines="6" title="Deserializing JSON before using as idempotency key"
--8<-- "docs/examples/utilities/jmespath_functions/powertools_json_jmespath_function_idempotency.py"
```

#### powertools_base64 function

Use `powertools_base64` function to decode any base64 data.

This sample will decode the base64 value within the `data` key, and decode the JSON string into a valid JSON before we can validate it.

=== "powertools_base64_jmespath_function.py"

    ```python hl_lines="12"
    --8<-- "docs/examples/utilities/jmespath_functions/powertools_base64_jmespath_function.py"
    ```

=== "schemas.py"

    ```python hl_lines="8 10 17 34 36 41"
    --8<-- "docs/shared/validation_basic_jsonschema.py"
    ```

#### powertools_base64_gzip function

Use `powertools_base64_gzip` function to decompress and decode base64 data.

This sample will decompress and decode base64 data, then use JMESPath pipeline expression to pass the result for decoding its JSON string.

=== "powertools_base64_gzip_jmespath_function.py"

    ```python hl_lines="12"
    --8<-- "docs/examples/utilities/jmespath_functions/powertools_base64_gzip_jmespath_function.py"
    ```

=== "schemas.py"

    ```python hl_lines="8 10 17 34 36 41"
    --8<-- "docs/shared/validation_basic_jsonschema.py"
    ```

### Bring your own JMESPath function

???+ warning
    This should only be used for advanced use cases where you have special formats not covered by the built-in functions.

For special binary formats that you want to decode before applying JSON Schema validation, you can bring your own [JMESPath function](https://github.com/jmespath/jmespath.py#custom-functions){target="_blank"} and any additional option via `jmespath_options` param.

In order to keep the built-in functions from Powertools, you can subclass from `PowertoolsFunctions`:

=== "custom_jmespath_function.py"

    ```python hl_lines="1 3 6-9 12 20"
    --8<-- "docs/examples/utilities/jmespath_functions/custom_jmespath_function.py"
    ```

=== "event.json"

    ```json
    	{"body": "custom_encoded_data"}
    ```
