---
title: JMESPath Functions
description: Utility
---

<!-- markdownlint-disable MD043 -->

???+ tip
    JMESPath is a query language for JSON used by AWS CLI, AWS Python SDK, and AWS Lambda Powertools for Python.

Built-in [JMESPath](https://jmespath.org/){target="_blank"} Functions to easily deserialize common encoded JSON payloads in Lambda functions.

## Key features

* Deserialize JSON from JSON strings, base64, and compressed data
* Use JMESPath to extract and combine data recursively

## Getting started

???+ tip
    All examples shared in this documentation are available within the [project repository](https://github.com/awslabs/aws-lambda-powertools-python/tree/develop/examples){target="_blank"}.

You might have events that contains encoded JSON payloads as string, base64, or even in compressed format. It is a common use case to decode and extract them partially or fully as part of your Lambda function invocation.

Lambda Powertools also have utilities like [validation](validation.md), [idempotency](idempotency.md), or [feature flags](feature_flags.md) where you might need to extract a portion of your data before using them.

???+ info
    **Envelope** is the terminology we use for the JMESPath expression to extract your JSON object from your data input.

### Extracting data

You can use the `extract_data_from_envelope` function along with any [JMESPath expression](https://jmespath.org/tutorial.html){target="_blank"}.

???+ tip
	Another common use case is to fetch deeply nested data, filter, flatten, and more.

=== "extract_data_from_envelope.py"
    ```python hl_lines="1 6 10"
    --8<-- "examples/jmespath_functions/src/extract_data_from_envelope.py"
    ```

=== "extract_data_from_envelope.json"

    ```json
    --8<-- "examples/jmespath_functions/src/extract_data_from_envelope.json"
    ```

### Built-in envelopes

We provide built-in envelopes for popular JMESPath expressions used when looking to decode/deserialize JSON objects within AWS Lambda Event Sources.

=== "extract_data_from_builtin_envelope.py"

	```python hl_lines="1 6"
    --8<-- "examples/jmespath_functions/src/extract_data_from_builtin_envelope.py"
	```

=== "extract_data_from_builtin_envelope.json"

    ```json hl_lines="6 15"
    --8<-- "examples/jmespath_functions/src/extract_data_from_builtin_envelope.json"
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

    ```python hl_lines="7"
    --8<-- "examples/jmespath_functions/src/powertools_json_jmespath_function.py"
    ```

=== "powertools_json_jmespath_schema.py"

    ```python hl_lines="7 14 16 23 39 45 47 52"
    --8<-- "examples/jmespath_functions/src/powertools_json_jmespath_schema.py"
    ```

> **Idempotency scenario**

This sample will decode the value within the `body` key of an API Gateway event into a valid JSON object to ensure the Idempotency utility processes a JSON object instead of a string.

=== "powertools_json_idempotency_jmespath.py"

    ```python hl_lines="9"
    --8<-- "examples/jmespath_functions/src/powertools_json_idempotency_jmespath.py"
    ```

=== "powertools_json_idempotency_jmespath.json"

    ```json hl_lines="28"
    --8<-- "examples/jmespath_functions/src/powertools_json_idempotency_jmespath.json"
    ```

#### powertools_base64 function

Use `powertools_base64` function to decode any base64 data.

This sample will decode the base64 value within the `data` key, and decode the JSON string into a valid JSON before we can validate it.

=== "powertools_base64_jmespath_function.py"

    ```python hl_lines="7"
    --8<-- "examples/jmespath_functions/src/powertools_base64_jmespath_function.py"
    ```

=== "powertools_base64_jmespath_schema.py"

    ```python hl_lines="7 14 16 23 39 45 47 52"
    --8<-- "examples/jmespath_functions/src/powertools_base64_jmespath_schema.py"
    ```

#### powertools_base64_gzip function

Use `powertools_base64_gzip` function to decompress and decode base64 data.

This sample will decompress and decode base64 data, then use JMESPath pipeline expression to pass the result for decoding its JSON string.

=== "powertools_base64_gzip_jmespath_function.py"

    ```python hl_lines="9"
    --8<-- "examples/jmespath_functions/src/powertools_base64_gzip_jmespath_function.py"
    ```

=== "powertools_base64_gzip_jmespath_schema.py"

    ```python hl_lines="7 14 16 23 39 45 47 52"
    --8<-- "examples/jmespath_functions/src/powertools_base64_gzip_jmespath_schema.py"
    ```

### Bring your own JMESPath function

???+ warning
    This should only be used for advanced use cases where you have special formats not covered by the built-in functions.

For special binary formats that you want to decode before applying JSON Schema validation, you can bring your own [JMESPath function](https://github.com/jmespath/jmespath.py#custom-functions){target="_blank"} and any additional option via `jmespath_options` param.

In order to keep the built-in functions from Powertools, you can subclass from `PowertoolsFunctions`:

=== "powertools_custom_jmespath_function.py"

    ```python hl_lines="3 5 8-12 15 20"
	--8<-- "examples/jmespath_functions/src/powertools_custom_jmespath_function.py"
    ```

=== "powertools_custom_jmespath_function.json"

    ```json
    --8<-- "examples/jmespath_functions/src/powertools_custom_jmespath_function.json"
    ```
