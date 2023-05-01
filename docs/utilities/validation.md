---
title: Validation
description: Utility
---

<!-- markdownlint-disable MD043 -->

This utility provides JSON Schema validation for events and responses, including JMESPath support to unwrap events before validation.

## Key features

* Validate incoming event and response
* JMESPath support to unwrap events before validation applies
* Built-in envelopes to unwrap popular event sources payloads

## Getting started

???+ tip
    All examples shared in this documentation are available within the [project repository](https://github.com/awslabs/aws-lambda-powertools-python/tree/develop/examples){target="_blank"}.

You can validate inbound and outbound events using [`validator` decorator](#validator-decorator).

You can also use the standalone `validate` function, if you want more control over the validation process such as handling a validation error.

???+ tip "Tip: Using JSON Schemas for the first time?"
    Check this [step-by-step tour in the official JSON Schema website](https://json-schema.org/learn/getting-started-step-by-step.html){target="_blank"}.

    We support any JSONSchema draft supported by [fastjsonschema](https://horejsek.github.io/python-fastjsonschema/){target="_blank"} library.

???+ warning
    Both `validator` decorator and `validate` standalone function expects your JSON Schema to be a **dictionary**, not a filename.

### Install

!!! info "This is not necessary if you're installing Powertools via [Lambda Layer/SAR](../index.md#lambda-layer){target="_blank"}"

Add `aws-lambda-powertools[validation]` as a dependency in your preferred tool: _e.g._, _requirements.txt_, _pyproject.toml_. This will ensure you have the required dependencies before using Validation.

### Validator decorator

**Validator** decorator is typically used to validate either inbound or functions' response.

It will fail fast with `SchemaValidationError` exception if event or response doesn't conform with given JSON Schema.

=== "getting_started_validator_decorator_function.py"

	```python hl_lines="8 27 28 42"
    --8<-- "examples/validation/src/getting_started_validator_decorator_function.py"
	```

=== "getting_started_validator_decorator_schema.py"

	```python hl_lines="10 12 17 19 24 26 28 44 46 51 53"
    --8<-- "examples/validation/src/getting_started_validator_decorator_schema.py"
	```

=== "getting_started_validator_decorator_payload.json"

    ```json
    --8<-- "examples/validation/src/getting_started_validator_decorator_payload.json"
    ```

???+ note
    It's not a requirement to validate both inbound and outbound schemas - You can either use one, or both.

### Validate function

**Validate** standalone function is typically used within the Lambda handler, or any other methods that perform data validation.

You can also gracefully handle schema validation errors by catching `SchemaValidationError` exception.

=== "getting_started_validator_standalone_function.py"

	```python hl_lines="5 16 17 26"
    --8<-- "examples/validation/src/getting_started_validator_standalone_function.py"
	```

=== "getting_started_validator_standalone_schema.py"

	```python hl_lines="7 8 10 12 17 19 24 26 28"
    --8<-- "examples/validation/src/getting_started_validator_standalone_schema.py"
	```

=== "getting_started_validator_standalone_payload.json"

    ```json
    --8<-- "examples/validation/src/getting_started_validator_standalone_payload.json"
    ```

### Unwrapping events prior to validation

You might want to validate only a portion of your event - This is what the `envelope` parameter is for.

Envelopes are [JMESPath expressions](https://jmespath.org/tutorial.html) to extract a portion of JSON you want before applying JSON Schema validation.

Here is a sample custom EventBridge event, where we only validate what's inside the `detail` key:

=== "getting_started_validator_unwrapping_function.py"

	```python hl_lines="2 8 14"
    --8<-- "examples/validation/src/getting_started_validator_unwrapping_function.py"
	```

=== "getting_started_validator_unwrapping_schema.py"

	```python hl_lines="9-14 23 25 28 33 36 41 44 48 51"
    --8<-- "examples/validation/src/getting_started_validator_unwrapping_schema.py"
	```

=== "getting_started_validator_unwrapping_payload.json"

    ```json
    --8<-- "examples/validation/src/getting_started_validator_unwrapping_payload.json"
    ```

This is quite powerful because you can use JMESPath Query language to extract records from [arrays](https://jmespath.org/tutorial.html#list-and-slice-projections), combine [pipe](https://jmespath.org/tutorial.html#pipe-expressions) and [function expressions](https://jmespath.org/tutorial.html#functions).

When combined, these features allow you to extract what you need before validating the actual payload.

### Built-in envelopes

We provide built-in envelopes to easily extract the payload from popular event sources.

=== "unwrapping_popular_event_source_function.py"

	```python hl_lines="2 9 14"
    --8<-- "examples/validation/src/unwrapping_popular_event_source_function.py"
	```

=== "unwrapping_popular_event_source_schema.py"

	```python hl_lines="7 9 12 17 20"
    --8<-- "examples/validation/src/unwrapping_popular_event_source_schema.py"
	```

=== "unwrapping_popular_event_source_payload.json"

    ```json hl_lines="12 13"
    --8<-- "examples/validation/src/unwrapping_popular_event_source_payload.json"
    ```

Here is a handy table with built-in envelopes along with their JMESPath expressions in case you want to build your own.

| Envelope                          | JMESPath expression                                                      |
| --------------------------------- | ------------------------------------------------------------------------ |
| **`API_GATEWAY_HTTP`**            | `powertools_json(body)`                                                  |
| **`API_GATEWAY_REST`**            | `powertools_json(body)`                                                  |
| **`CLOUDWATCH_EVENTS_SCHEDULED`** | `detail`                                                                 |
| **`CLOUDWATCH_LOGS`**             | `awslogs.powertools_base64_gzip(data) | powertools_json(@).logEvents[*]` |
| **`EVENTBRIDGE`**                 | `detail`                                                                 |
| **`KINESIS_DATA_STREAM`**         | `Records[*].kinesis.powertools_json(powertools_base64(data))`            |
| **`SNS`**                         | `Records[0].Sns.Message | powertools_json(@)`                            |
| **`SQS`**                         | `Records[*].powertools_json(body)`                                       |

## Advanced

### Validating custom formats

???+ note
    JSON Schema DRAFT 7 [has many new built-in formats](https://json-schema.org/understanding-json-schema/reference/string.html#format){target="_blank"} such as date, time, and specifically a regex format which might be a better replacement for a custom format, if you do have control over the schema.

JSON Schemas with custom formats like `awsaccountid` will fail validation. If you have these, you can pass them using `formats` parameter:

```json title="custom_json_schema_type_format.json"
{
	"accountid": {
		"format": "awsaccountid",
		"type": "string"
	}
}
```

For each format defined in a dictionary key, you must use a regex, or a function that returns a boolean to instruct the validator on how to proceed when encountering that type.

=== "custom_format_function.py"

	```python hl_lines="5 8 10 11 17 27"
    --8<-- "examples/validation/src/custom_format_function.py"
	```

=== "custom_format_schema.py"

	```python hl_lines="7 9 12 13 17 20"
    --8<-- "examples/validation/src/custom_format_schema.py"
	```

=== "custom_format_payload.json"

    ```json hl_lines="12 13"
    --8<-- "examples/validation/src/custom_format_payload.json"
    ```

### Built-in JMESPath functions

You might have events or responses that contain non-encoded JSON, where you need to decode before validating them.

You can use our built-in [JMESPath functions](./jmespath_functions.md) within your expressions to do exactly that to [deserialize JSON Strings](./jmespath_functions.md#powertools_json-function), [decode base64](./jmespath_functions.md#powertools_base64-function), and [decompress gzip data](./jmespath_functions.md#powertools_base64_gzip-function).

???+ info
    We use these for [built-in envelopes](#built-in-envelopes) to easily to decode and unwrap events from sources like Kinesis, CloudWatch Logs, etc.
