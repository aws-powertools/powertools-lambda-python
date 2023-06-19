---
title: JMESPath Functions
description: Utility
---

<!-- markdownlint-disable MD043 -->

???+ tip
    JMESPath is a query language for JSON used by AWS CLI, AWS Python SDK, and Powertools for AWS Lambda (Python).

Built-in [JMESPath](https://jmespath.org/){target="_blank"} Functions to easily deserialize common encoded JSON payloads in Lambda functions.

## Key features

* Deserialize JSON from JSON strings, base64, and compressed data
* Use JMESPath to extract and combine data recursively
* Provides commonly used JMESPath expression with popular event sources

## Getting started

???+ tip
    All examples shared in this documentation are available within the [project repository](https://github.com/aws-powertools/powertools-lambda-python/tree/develop/examples){target="_blank"}.

You might have events that contains encoded JSON payloads as string, base64, or even in compressed format. It is a common use case to decode and extract them partially or fully as part of your Lambda function invocation.

Powertools for AWS Lambda (Python) also have utilities like [validation](validation.md){target="_blank"}, [idempotency](idempotency.md){target="_blank"}, or [feature flags](feature_flags.md){target="_blank"} where you might need to extract a portion of your data before using them.

???+ info "Terminology"
    **Envelope** is the terminology we use for the **JMESPath expression** to extract your JSON object from your data input. We might use those two terms interchangeably.

### Extracting data

You can use the `extract_data_from_envelope` function with any [JMESPath expression](https://jmespath.org/tutorial.html){target="_blank"}.

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

We provide built-in envelopes for popular AWS Lambda event sources to easily decode and/or deserialize JSON objects.

=== "extract_data_from_builtin_envelope.py"

	```python hl_lines="1-4 9"
    --8<-- "examples/jmespath_functions/src/extract_data_from_builtin_envelope.py"
	```

=== "extract_data_from_builtin_envelope.json"

    ```json hl_lines="6 15"
    --8<-- "examples/jmespath_functions/src/extract_data_from_builtin_envelope.json"
    ```

These are all built-in envelopes you can use along with their expression as a reference:

| Envelope                          | JMESPath expression                                                                       |
| --------------------------------- | ----------------------------------------------------------------------------------------- |
| **`API_GATEWAY_HTTP`**            | `powertools_json(body)`                                                                   |
| **`API_GATEWAY_REST`**            | `powertools_json(body)`                                                                   |
| **`CLOUDWATCH_EVENTS_SCHEDULED`** | `detail`                                                                                  |
| **`CLOUDWATCH_LOGS`**             | `awslogs.powertools_base64_gzip(data)                                                     | powertools_json(@).logEvents[*]` |
| **`EVENTBRIDGE`**                 | `detail`                                                                                  |
| **`KINESIS_DATA_STREAM`**         | `Records[*].kinesis.powertools_json(powertools_base64(data))`                             |
| **`S3_EVENTBRIDGE_SQS`**          | `Records[*].powertools_json(body).detail`                                                 |
| **`S3_KINESIS_FIREHOSE`**         | `records[*].powertools_json(powertools_base64(data)).Records[0]`                          |
| **`S3_SNS_KINESIS_FIREHOSE`**     | `records[*].powertools_json(powertools_base64(data)).powertools_json(Message).Records[0]` |
| **`S3_SNS_SQS`**                  | `Records[*].powertools_json(body).powertools_json(Message).Records[0]`                    |
| **`S3_SQS`**                      | `Records[*].powertools_json(body).Records[0]`                                             |
| **`SNS`**                         | `Records[0].Sns.Message                                                                   | powertools_json(@)`              |
| **`SQS`**                         | `Records[*].powertools_json(body)`                                                        |

???+ tip "Using SNS?"
    If you don't require SNS metadata, enable [raw message delivery](https://docs.aws.amazon.com/sns/latest/dg/sns-large-payload-raw-message-delivery.html). It will reduce multiple payload layers and size, when using SNS in combination with other services (_e.g., SQS, S3, etc_).

## Advanced

### Built-in JMESPath functions

You can use our built-in JMESPath functions within your envelope expression. They handle deserialization for common data formats found in AWS Lambda event sources such as JSON strings, base64, and uncompress gzip data.

???+ info
    We use these everywhere in Powertools for AWS Lambda (Python) to easily decode and unwrap events from Amazon API Gateway, Amazon Kinesis, AWS CloudWatch Logs, etc.

#### powertools_json function

Use `powertools_json` function to decode any JSON string anywhere a JMESPath expression is allowed.

> **Validation scenario**

This sample will deserialize the JSON string within the `data` key before validation.

=== "powertools_json_jmespath_function.py"

    ```python hl_lines="5 8 34 45 48 51"
    --8<-- "examples/jmespath_functions/src/powertools_json_jmespath_function.py"
    ```

=== "powertools_json_jmespath_schema.py"

    ```python hl_lines="7 8 10 12 17 19 24 26 31 33 38 40"
    --8<-- "examples/jmespath_functions/src/powertools_json_jmespath_schema.py"
    ```

=== "powertools_json_jmespath_payload.json"

    ```json
    --8<-- "examples/jmespath_functions/src/powertools_json_jmespath_payload.json"
    ```

> **Idempotency scenario**

This sample will deserialize the JSON string within the `body` key before [Idempotency](./idempotency.md){target="_blank"} processes it.

=== "powertools_json_idempotency_jmespath.py"

    ```python hl_lines="16"
    --8<-- "examples/jmespath_functions/src/powertools_json_idempotency_jmespath.py"
    ```

=== "powertools_json_idempotency_jmespath.json"

    ```json hl_lines="28"
    --8<-- "examples/jmespath_functions/src/powertools_json_idempotency_jmespath.json"
    ```

#### powertools_base64 function

Use `powertools_base64` function to decode any base64 data.

This sample will decode the base64 value within the `data` key, and deserialize the JSON string before validation.

=== "powertools_base64_jmespath_function.py"

    ```python hl_lines="7 10 37 49 53 55 57"
    --8<-- "examples/jmespath_functions/src/powertools_base64_jmespath_function.py"
    ```

=== "powertools_base64_jmespath_schema.py"

    ```python hl_lines="7 8 10 12 17 19 24 26 31 33 38 40"
    --8<-- "examples/jmespath_functions/src/powertools_base64_jmespath_schema.py"
    ```

=== "powertools_base64_jmespath_payload.json"

    ```json
    --8<-- "examples/jmespath_functions/src/powertools_base64_jmespath_payload.json"
    ```

#### powertools_base64_gzip function

Use `powertools_base64_gzip` function to decompress and decode base64 data.

This sample will decompress and decode base64 data from Cloudwatch Logs, then use JMESPath pipeline expression to pass the result for decoding its JSON string.

=== "powertools_base64_gzip_jmespath_function.py"

    ```python hl_lines="6 10 15 29 31 33 35"
    --8<-- "examples/jmespath_functions/src/powertools_base64_gzip_jmespath_function.py"
    ```

=== "powertools_base64_gzip_jmespath_schema.py"

    ```python hl_lines="7-15 17 19 24 26 31 33 38 40"
    --8<-- "examples/jmespath_functions/src/powertools_base64_gzip_jmespath_schema.py"
    ```

=== "powertools_base64_gzip_jmespath_payload.json"

    ```json
    --8<-- "examples/jmespath_functions/src/powertools_base64_gzip_jmespath_payload.json"
    ```

### Bring your own JMESPath function

???+ warning
    This should only be used for advanced use cases where you have special formats not covered by the built-in functions.

For special binary formats that you want to decode before applying JSON Schema validation, you can bring your own [JMESPath function](https://github.com/jmespath/jmespath.py#custom-functions){target="_blank"} and any additional option via `jmespath_options` param. To keep Powertools for AWS Lambda (Python) built-in functions, you can subclass from `PowertoolsFunctions`.

Here is an example of how to decompress messages using [snappy](https://github.com/andrix/python-snappy){target="_blank"}:

=== "powertools_custom_jmespath_function.py"

    ```python hl_lines="9 14 17-18 23 34 39 41 43"
	--8<-- "examples/jmespath_functions/src/powertools_custom_jmespath_function.py"
    ```

=== "powertools_custom_jmespath_function.json"

    ```json
    --8<-- "examples/jmespath_functions/src/powertools_custom_jmespath_function.json"
    ```
