---
title: Parser
description: Utility
---

This utility provides data parsing and deep validation using [Pydantic](https://pydantic-docs.helpmanual.io/).

## Key features

* Defines data in pure Python classes, then parse, validate and extract only what you want
* Built-in envelopes to unwrap, extend, and validate popular event sources payloads
* Enforces type hints at runtime with user-friendly errors

**Extra dependency**

???+ warning

    This will increase the compressed package size by >10MB due to the Pydantic dependency.

    To reduce the impact on the package size at the expense of 30%-50% of its performance [Pydantic can also be
    installed without binary files](https://pydantic-docs.helpmanual.io/install/#performance-vs-package-size-trade-off):

    `SKIP_CYTHON=1 pip install --no-binary pydantic aws-lambda-powertools[pydantic]`

Install parser's extra dependencies using **`pip install aws-lambda-powertools[pydantic]`**.

## Defining models

You can define models to parse incoming events by inheriting from `BaseModel`.

```python title="Defining an Order data model"
--8<-- "docs/examples/utilities/parser/parser_models.py"
```

These are simply Python classes that inherit from BaseModel. **Parser** enforces type hints declared in your model at runtime.

## Parsing events

You can parse inbound events using **event_parser** decorator, or the standalone `parse` function. Both are also able to parse either dictionary or JSON string as an input.

### event_parser decorator

Use the decorator for fail fast scenarios where you want your Lambda function to raise an exception in the event of a malformed payload.

`event_parser` decorator will throw a `ValidationError` if your event cannot be parsed according to the model.

???+ note
    **This decorator will replace the `event` object with the parsed model if successful**. This means you might be careful when nesting other decorators that expect `event` to be a `dict`.

```python hl_lines="21" title="Parsing and validating upon invocation with event_parser decorator"
--8<-- "docs/examples/utilities/parser/parser_event_parser_decorator.py"
```

### parse function

Use this standalone function when you want more control over the data validation process, for example returning a 400 error for malformed payloads.

```python hl_lines="24 35" title="Using standalone parse function for more flexibility"
--8<-- "docs/examples/utilities/parser/parser_parse_function.py"
```

## Built-in models

Parser comes with the following built-in models:

| Model name                        | Description                                                        |
| --------------------------------- | ------------------------------------------------------------------ |
| **DynamoDBStreamModel**           | Lambda Event Source payload for Amazon DynamoDB Streams            |
| **EventBridgeModel**              | Lambda Event Source payload for Amazon EventBridge                 |
| **SqsModel**                      | Lambda Event Source payload for Amazon SQS                         |
| **AlbModel**                      | Lambda Event Source payload for Amazon Application Load Balancer   |
| **CloudwatchLogsModel**           | Lambda Event Source payload for Amazon CloudWatch Logs             |
| **S3Model**                       | Lambda Event Source payload for Amazon S3                          |
| **S3ObjectLambdaEvent**           | Lambda Event Source payload for Amazon S3 Object Lambda            |
| **KinesisDataStreamModel**        | Lambda Event Source payload for Amazon Kinesis Data Streams        |
| **SesModel**                      | Lambda Event Source payload for Amazon Simple Email Service        |
| **SnsModel**                      | Lambda Event Source payload for Amazon Simple Notification Service |
| **APIGatewayProxyEventModel**     | Lambda Event Source payload for Amazon API Gateway                 |
| **APIGatewayProxyEventV2Model**   | Lambda Event Source payload for Amazon API Gateway v2 payload      |

### extending built-in models

You can extend them to include your own models, and yet have all other known fields parsed along the way.

???+ tip
    For Mypy users, we only allow type override for fields where payload is injected e.g. `detail`, `body`, etc.

```python hl_lines="19-20 32 45" title="Extending EventBridge model as an example"
--8<-- "docs/examples/utilities/parser/parser_extending_builtin_models.py"
```

**What's going on here, you might ask**:

1. We imported our built-in model `EventBridgeModel` from the parser utility
2. Defined how our `Order` should look like
3. Defined how part of our EventBridge event should look like by overriding `detail` key within our `OrderEventModel`
4. Parser parsed the original event against `OrderEventModel`

## Envelopes

When trying to parse your payloads wrapped in a known structure, you might encounter the following situations:

* Your actual payload is wrapped around a known structure, for example Lambda Event Sources like EventBridge
* You're only interested in a portion of the payload, for example parsing the `detail` of custom events in EventBridge, or `body` of SQS records

You can either solve these situations by creating a model of these known structures, parsing them, then extracting and parsing a key where your payload is.

This can become difficult quite quickly. Parser makes this problem easier through a feature named `Envelope`.

Envelopes can be used via `envelope` parameter available in both `parse` function and `event_parser` decorator.

Here's an example of parsing a model found in an event coming from EventBridge, where all you want is what's inside the `detail` key.

```python hl_lines="20-24 27 33" title="Parsing payload in a given key only using envelope feature"
--8<-- "docs/examples/utilities/parser/parser_envelope.py"
```

**What's going on here, you might ask**:

1. We imported built-in `envelopes` from the parser utility
2. Used `envelopes.EventBridgeEnvelope` as the envelope for our `UserModel` model
3. Parser parsed the original event against the EventBridge model
4. Parser then parsed the `detail` key using `UserModel`

### Built-in envelopes

Parser comes with the following built-in envelopes, where `Model` in the return section is your given model.

| Envelope name                 | Behaviour                                                                                                                                                                                                   | Return                             |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| **DynamoDBStreamEnvelope**    | 1. Parses data using `DynamoDBStreamModel`. <br/> 2. Parses records in `NewImage` and `OldImage` keys using your model. <br/> 3. Returns a list with a dictionary containing `NewImage` and `OldImage` keys | `List[Dict[str, Optional[Model]]]` |
| **EventBridgeEnvelope**       | 1. Parses data using `EventBridgeModel`. <br/> 2. Parses `detail` key using your model and returns it.                                                                                                      | `Model`                            |
| **SqsEnvelope**               | 1. Parses data using `SqsModel`. <br/> 2. Parses records in `body` key using your model and return them in a list.                                                                                          | `List[Model]`                      |
| **CloudWatchLogsEnvelope**    | 1. Parses data using `CloudwatchLogsModel` which will base64 decode and decompress it. <br/> 2. Parses records in `message` key using your model and return them in a list.                                 | `List[Model]`                      |
| **KinesisDataStreamEnvelope** | 1. Parses data using `KinesisDataStreamModel` which will base64 decode it. <br/> 2. Parses records in in `Records` key using your model and returns them in a list.                                         | `List[Model]`                      |
| **SnsEnvelope**               | 1. Parses data using `SnsModel`. <br/> 2. Parses records in `body` key using your model and return them in a list.                                                                                          | `List[Model]`                      |
| **SnsSqsEnvelope**            | 1. Parses data using `SqsModel`. <br/> 2. Parses SNS records in `body` key using `SnsNotificationModel`. <br/> 3. Parses data in `Message` key using your model and return them in a list.                  | `List[Model]`                      |
| **ApiGatewayEnvelope**        | 1. Parses data using `APIGatewayProxyEventModel`. <br/> 2. Parses `body` key using your model and returns it.                                                                                               | `Model`                            |
| **ApiGatewayV2Envelope**      | 1. Parses data using `APIGatewayProxyEventV2Model`. <br/> 2. Parses `body` key using your model and returns it.                                                                                             | `Model`                            |

### Bringing your own envelope

You can create your own Envelope model and logic by inheriting from `BaseEnvelope`, and implementing the `parse` method.

Here's a snippet of how the EventBridge envelope we demonstrated previously is implemented.

=== "EventBridge Model"

    ```python
	--8<-- "docs/examples/utilities/parser/parser_event_bridge_model.py"
    ```

=== "EventBridge Envelope"

    ```python hl_lines="9-10 25 26"
	--8<-- "docs/examples/utilities/parser/parser_event_bridge_envelope.py"
    ```

**What's going on here, you might ask**:

1. We defined an envelope named `EventBridgeEnvelope` inheriting from `BaseEnvelope`
2. Implemented the `parse` abstract method taking `data` and `model` as parameters
3. Then, we parsed the incoming data with our envelope to confirm it matches EventBridge's structure defined in `EventBridgeModel`
4. Lastly, we call `_parse` from `BaseEnvelope` to parse the data in our envelope (.detail) using the customer model

## Data model validation

???+ warning
    This is radically different from the **Validator utility** which validates events against JSON Schema.

You can use parser's validator for deep inspection of object values and complex relationships.

There are two types of class method decorators you can use:

* **`validator`** - Useful to quickly validate an individual field and its value
* **`root_validator`** - Useful to validate the entire model's data

Keep the following in mind regardless of which decorator you end up using it:

* You must raise either `ValueError`, `TypeError`, or `AssertionError` when value is not compliant
* You must return the value(s) itself if compliant

### validating fields

Quick validation to verify whether the field `message` has the value of `hello world`.

```python hl_lines="7" title="Data field validation with validator"
--8<-- "docs/examples/utilities/parser/parser_validator.py"
```

If you run as-is, you should expect the following error with the message we provided in our exception:

```python title="Sample validation error message"
message
  Message must be hello world! (type=value_error)
```

Alternatively, you can pass `'*'` as an argument for the decorator so that you can validate every value available.

```python hl_lines="8" title="Validating all data fields with custom logic"
--8<-- "docs/examples/utilities/parser/parser_validator_all.py"
```

### validating entire model

`root_validator` can help when you have a complex validation mechanism. For example finding whether data has been omitted, comparing field values, etc.

```python title="Comparing and validating multiple fields at once with root_validator"
--8<-- "docs/examples/utilities/parser/parser_validator_root.py"
```

???+ info
    You can read more about validating list items, reusing validators, validating raw inputs, and a lot more in <a href="https://pydantic-docs.helpmanual.io/usage/validators/">Pydantic's documentation</a>.

## Advanced use cases

???+ tip "Tip: Looking to auto-generate models from JSON, YAML, JSON Schemas, OpenApi, etc?"
    Use Koudai Aono's [data model code generation tool for Pydantic](https://github.com/koxudaxi/datamodel-code-generator)

There are number of advanced use cases well documented in Pydantic's doc such as creating [immutable models](https://pydantic-docs.helpmanual.io/usage/models/#faux-immutability), [declaring fields with dynamic values](https://pydantic-docs.helpmanual.io/usage/models/#field-with-dynamic-default-value)) e.g. UUID, and [helper functions to parse models from files, str](https://pydantic-docs.helpmanual.io/usage/models/#helper-functions), etc.

Two possible unknown use cases are Models and exception' serialization. Models have methods to [export them](https://pydantic-docs.helpmanual.io/usage/exporting_models/) as `dict`, `JSON`, `JSON Schema`, and Validation exceptions can be exported as JSON.

```python hl_lines="24 29-32" title="Converting data models in various formats"
--8<-- "docs/examples/utilities/parser/parser_model_export.py"
```

These can be quite useful when manipulating models that later need to be serialized as inputs for services like DynamoDB, EventBridge, etc.

## FAQ

**When should I use parser vs data_classes utility?**

Use data classes utility when you're after autocomplete, self-documented attributes and helpers to extract data from common event sources.

Parser is best suited for those looking for a trade-off between defining their models for deep validation, parsing and autocomplete for an additional dependency to be brought in.

**How do I import X from Pydantic?**

We export most common classes, exceptions, and utilities from Pydantic as part of parser e.g. `from aws_lambda_powertools.utilities.parser import BaseModel`.

If what's your trying to use isn't available as part of the high level import system, use the following escape hatch mechanism:

```python title="Pydantic import escape hatch"
from aws_lambda_powertools.utilities.parser.pydantic import <what you'd like to import'>
```

**What is the cold start impact in bringing this additional dependency?**

No significant cold start impact. It does increase the final uncompressed package by **71M**, when you bring the additional dependency that parser requires.

Artillery load test sample against a [hello world sample](https://github.com/aws-samples/cookiecutter-aws-sam-python) using Tracer, Metrics, and Logger with and without parser.

**No parser**

???+ info
    **Uncompressed package size**: 55M, **p99**: 180.3ms

```
Summary report @ 14:36:07(+0200) 2020-10-23
Scenarios launched:  10
Scenarios completed: 10
Requests completed:  2000
Mean response/sec: 114.81
Response time (msec):
    min: 54.9
    max: 1684.9
    median: 68
    p95: 109.1
    p99: 180.3
Scenario counts:
    0: 10 (100%)
Codes:
    200: 2000
```

**With parser**

???+ info
    **Uncompressed package size**: 128M, **p99**: 193.1ms

```
Summary report @ 14:29:23(+0200) 2020-10-23
Scenarios launched:  10
Scenarios completed: 10
Requests completed:  2000
Mean response/sec: 111.67
Response time (msec):
    min: 54.3
    max: 1887.2
    median: 66.1
    p95: 113.3
    p99: 193.1
Scenario counts:
    0: 10 (100%)
Codes:
    200: 2000
```
