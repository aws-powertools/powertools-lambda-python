---
title: Validation
description: Utility
---


This utility provides JSON Schema validation for events and responses, including JMESPath support to unwrap events before validation.

**Key features**

* Validate incoming event and response
* JMESPath support to unwrap events before validation applies
* Built-in envelopes to unwrap popular event sources payloads

## Validating events

You can validate inbound and outbound events using `validator` decorator.

You can also use the standalone `validate` function, if you want more control over the validation process such as handling a validation error.

We support any JSONSchema draft supported by [fastjsonschema](https://horejsek.github.io/python-fastjsonschema/) library.

!!! warning
    Both `validator` decorator and `validate` standalone function expects your JSON Schema to be a **dictionary**, not a filename.


### Validator decorator

**Validator** decorator is typically used to validate either inbound or functions' response.

It will fail fast with `SchemaValidationError` exception if event or response doesn't conform with given JSON Schema.

=== "validator_decorator.py"

    ```python
    from aws_lambda_powertools.utilities.validation import validator

    json_schema_dict = {..}
    response_json_schema_dict = {..}

    @validator(inbound_schema=json_schema_dict, outbound_schema=response_json_schema_dict)
    def handler(event, context):
        return event
    ```

!!! note
    It's not a requirement to validate both inbound and outbound schemas - You can either use one, or both.

### Validate function

**Validate** standalone function is typically used within the Lambda handler, or any other methods that perform data validation.

You can also gracefully handle schema validation errors by catching `SchemaValidationError` exception.

=== "validator_decorator.py"

    ```python
    from aws_lambda_powertools.utilities.validation import validate
    from aws_lambda_powertools.utilities.validation.exceptions import SchemaValidationError

    json_schema_dict = {..}

    def handler(event, context):
        try:
            validate(event=event, schema=json_schema_dict)
        except SchemaValidationError as e:
            # do something before re-raising
            raise

        return event
    ```

### Validating custom formats

!!! note "New in 1.10.0"
    JSON Schema DRAFT 7 [has many new built-in formats](https://json-schema.org/understanding-json-schema/reference/string.html#format) such as date, time, and specifically a regex format which might be a better replacement for a custom format, if you do have control over the schema.

If you have JSON Schemas with custom formats, for example having a `int64` for high precision integers, you can pass an optional validation to handle each type using `formats` parameter - Otherwise it'll fail validation:

**Example of custom integer format**

```json
{
	"lastModifiedTime": {
	  "format": "int64",
	  "type": "integer"
	}
}
```

For each format defined in a dictionary key, you must use a regex, or a function that returns a boolean to instruct the validator on how to proceed when encountering that type.

```python
from aws_lambda_powertools.utilities.validation import validate

event = {} # some event
schema_with_custom_format = {} # some JSON schema that defines a custom format

custom_format = {
    "int64": True, # simply ignore it,
	"positive": lambda x: False if x < 0 else True
}

validate(event=event, schema=schema_with_custom_format, formats=custom_format)
```

## Unwrapping events prior to validation

You might want to validate only a portion of your event - This is where the `envelope` parameter is for.

Envelopes are [JMESPath expressions](https://jmespath.org/tutorial.html) to extract a portion of JSON you want before applying JSON Schema validation.

Here is a sample custom EventBridge event, where we only validate what's inside the `detail` key:

=== "sample_wrapped_event.json"

    ```json hl_lines="9"
    {
      "id": "cdc73f9d-aea9-11e3-9d5a-835b769c0d9c",
      "detail-type": "Scheduled Event",
      "source": "aws.events",
      "account": "123456789012",
      "time": "1970-01-01T00:00:00Z",
      "region": "us-east-1",
      "resources": ["arn:aws:events:us-east-1:123456789012:rule/ExampleRule"],
      "detail": {"message": "hello hello", "username": "blah blah"}
    }
    ```

Here is how you'd use the `envelope` parameter to extract the payload inside the `detail` key before validating:

=== "unwrapping_events.py"

    ```python hl_lines="5 7"
    from aws_lambda_powertools.utilities.validation import validator, validate

    json_schema_dict = {..}

    @validator(inbound_schema=json_schema_dict, envelope="detail")
    def handler(event, context):
        validate(event=event, schema=json_schema_dict, envelope="detail")
        return event
    ```

This is quite powerful because you can use JMESPath Query language to extract records from [arrays, slice and dice](https://jmespath.org/tutorial.html#list-and-slice-projections), to [pipe expressions](https://jmespath.org/tutorial.html#pipe-expressions) and [function expressions](https://jmespath.org/tutorial.html#functions), where you'd extract what you need before validating the actual payload.

## Built-in envelopes

This utility comes with built-in envelopes to easily extract the payload from popular event sources.

=== "unwrapping_popular_event_sources.py"

    ```python hl_lines="5 7"
    from aws_lambda_powertools.utilities.validation import envelopes, validate, validator

    json_schema_dict = {..}

    @validator(inbound_schema=json_schema_dict, envelope=envelopes.EVENTBRIDGE)
    def handler(event, context):
        validate(event=event, schema=json_schema_dict, envelope=envelopes.EVENTBRIDGE)
        return event
    ```

Here is a handy table with built-in envelopes along with their JMESPath expressions in case you want to build your own.

Envelope name | JMESPath expression
------------------------------------------------- | ---------------------------------------------------------------------------------
**API_GATEWAY_REST** | "powertools_json(body)"
**API_GATEWAY_HTTP** | "powertools_json(body)"
**SQS** | "Records[*].powertools_json(body)"
**SNS** | "Records[0].Sns.Message | powertools_json(@)"
**EVENTBRIDGE** | "detail"
**CLOUDWATCH_EVENTS_SCHEDULED** | "detail"
**KINESIS_DATA_STREAM** | "Records[*].kinesis.powertools_json(powertools_base64(data))"
**CLOUDWATCH_LOGS** | "awslogs.powertools_base64_gzip(data) | powertools_json(@).logEvents[*]"

## Built-in JMESPath functions

You might have events or responses that contain non-encoded JSON, where you need to decode before validating them.

You can use our built-in JMESPath functions within your expressions to do exactly that to decode JSON Strings, base64, and uncompress gzip data.

!!! info
    We use these for built-in envelopes to easily to decode and unwrap events from sources like Kinesis, CloudWatch Logs, etc.

### powertools_json function

Use `powertools_json` function to decode any JSON String.

This sample will decode the value within the `data` key into a valid JSON before we can validate it.

=== "powertools_json_jmespath_function.py"

    ```python hl_lines="9"
    from aws_lambda_powertools.utilities.validation import validate

    json_schema_dict = {..}
    sample_event = {
        'data': '{"payload": {"message": "hello hello", "username": "blah blah"}}'
    }

    def handler(event, context):
        validate(event=event, schema=json_schema_dict, envelope="powertools_json(data)")
        return event

    handler(event=sample_event, context={})
    ```

### powertools_base64 function

Use `powertools_base64` function to decode any base64 data.

This sample will decode the base64 value within the `data` key, and decode the JSON string into a valid JSON before we can validate it.

=== "powertools_json_jmespath_function.py"

    ```python hl_lines="9"
    from aws_lambda_powertools.utilities.validation import validate

    json_schema_dict = {..}
    sample_event = {
        "data": "eyJtZXNzYWdlIjogImhlbGxvIGhlbGxvIiwgInVzZXJuYW1lIjogImJsYWggYmxhaCJ9="
    }

    def handler(event, context):
        validate(event=event, schema=json_schema_dict, envelope="powertools_json(powertools_base64(data))")
        return event

    handler(event=sample_event, context={})
    ```

### powertools_base64_gzip function

Use `powertools_base64_gzip` function to decompress and decode base64 data.

This sample will decompress and decode base64 data, then use JMESPath pipeline expression to pass the result for decoding its JSON string.

=== "powertools_json_jmespath_function.py"

    ```python hl_lines="9"
    from aws_lambda_powertools.utilities.validation import validate

    json_schema_dict = {..}
    sample_event = {
        "data": "H4sIACZAXl8C/52PzUrEMBhFX2UILpX8tPbHXWHqIOiq3Q1F0ubrWEiakqTWofTdTYYB0YWL2d5zvnuTFellBIOedoiyKH5M0iwnlKH7HZL6dDB6ngLDfLFYctUKjie9gHFaS/sAX1xNEq525QxwFXRGGMEkx4Th491rUZdV3YiIZ6Ljfd+lfSyAtZloacQgAkqSJCGhxM6t7cwwuUGPz4N0YKyvO6I9WDeMPMSo8Z4Ca/kJ6vMEYW5f1MX7W1lVxaG8vqX8hNFdjlc0iCBBSF4ERT/3Pl7RbMGMXF2KZMh/C+gDpNS7RRsp0OaRGzx0/t8e0jgmcczyLCWEePhni/23JWalzjdu0a3ZvgEaNLXeugEAAA=="
    }

    def handler(event, context):
        validate(event=event, schema=json_schema_dict, envelope="powertools_base64_gzip(data) | powertools_json(@)")
        return event

    handler(event=sample_event, context={})
    ```

## Bring your own JMESPath function

!!! warning
    This should only be used for advanced use cases where you have special formats not covered by the built-in functions.

    This will **replace all provided built-in functions such as `powertools_json`, so you will no longer be able to use them**.

For special binary formats that you want to decode before applying JSON Schema validation, you can bring your own [JMESPath function](https://github.com/jmespath/jmespath.py#custom-functions) and any additional option via `jmespath_options` param.

=== "custom_jmespath_function.py"

    ```python hl_lines="15"
    from aws_lambda_powertools.utilities.validation import validate
    from jmespath import functions

    json_schema_dict = {..}

    class CustomFunctions(functions.Functions):

        @functions.signature({'types': ['string']})
        def _func_special_decoder(self, s):
            return my_custom_decoder_logic(s)

    custom_jmespath_options = {"custom_functions": CustomFunctions()}

    def handler(event, context):
        validate(event=event, schema=json_schema_dict, envelope="", jmespath_options=**custom_jmespath_options)
        return event
    ```
