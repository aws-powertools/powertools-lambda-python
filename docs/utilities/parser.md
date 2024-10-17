---
title: Parser (Pydantic)
description: Utility
---

<!-- markdownlint-disable MD043 -->

The Parser utility simplifies data parsing and validation using [Pydantic](https://pydantic-docs.helpmanual.io/){target="\_blank" rel="nofollow"}. It allows you to define data models in pure Python classes, parse and validate incoming events, and extract only the data you need.

## Key features

- Define data models using Python classes
- Parse and validate Lambda event payloads
- Built-in support for common AWS event sources
- Runtime type checking with user-friendly error messages
- Compatible with Pydantic v2

## Getting started

### Install

Parser supports Pydantic v2. Each Pydantic version requires different dependencies before you can use Parser.

```python
pip install aws-lambda-powertools
```

!!! info "This is not necessary if you're installing Powertools for AWS Lambda (Python) via [Lambda Layer/SAR](../index.md#lambda-layer){target="\_blank"}"

???+ warning
    This will increase the compressed package size by >10MB due to the Pydantic dependency.

    To reduce the impact on the package size at the expense of 30%-50% of its performance[Pydantic can also be
    installed without binary files](https://pydantic-docs.helpmanual.io/install/#performance-vs-package-size-trade-off){target="_blank" rel="nofollow"}:

    Pip example:`SKIP_CYTHON=1 pip install --no-binary pydantic aws-lambda-powertools[parser]`


You can also add as a dependency in your preferred tool: e.g., requirements.txt, pyproject.toml.

### Data Model with Parse

Define models by inheriting from `BaseModel` to parse incoming events. Pydantic then validates the data, ensuring all fields adhere to specified types and guaranteeing data integrity.

#### Event parser

The `event_parser` decorator automatically parses and validates the event.


```python title="getting_started_with_parser.py"
--8<-- "examples/parser/src/getting_started_with_parser.py"
```

The `@event_parser(model=MyEvent)` automatically parses the event into the specified Pydantic model MyEvent.

The function catches **ValidationError**, returning a 400 status code with an error message if the input doesn't match the `MyEvent` model. It provides robust error handling for invalid inputs.

#### Parse function

The `parse()` function allows you to manually control when and how an event is parsed into a Pydantic model. This can be useful in cases where you need flexibility, such as handling different event formats or adding custom logic before parsing.

```python title="parser_function.py"
--8<-- "examples/parser/src/parser_function.py"
```
---

**Should I use parse() or @event_parser? 🤔**

The `parse()` function offers more flexibility and control:

- It allows parsing different parts of an event using multiple models.
- You can conditionally handle events before parsing them.
- It's useful for integrating with complex workflows where a decorator might not be sufficient.
- It provides more control over the validation process.

The `@event_parser` decorator is ideal for:

- Fail-fast scenarios where you want to immediately stop execution if the event payload is invalid.
- Simplifying your code by automatically parsing and validating the event at the function entry point.

### Built-in models

Parser provides built-in models for parsing events from AWS services. You don't need to worry about creating these models yourself - we've already done that for you, making it easier to process AWS events in your Lambda functions.

| Model name                                  | Description                                                                           |
| ------------------------------------------- | ------------------------------------------------------------------------------------- |
| **AlbModel**                                | Lambda Event Source payload for Amazon Application Load Balancer                      |
| **APIGatewayProxyEventModel**               | Lambda Event Source payload for Amazon API Gateway                                    |
| **ApiGatewayAuthorizerToken**               | Lambda Event Source payload for Amazon API Gateway Lambda Authorizer with Token       |
| **ApiGatewayAuthorizerRequest**             | Lambda Event Source payload for Amazon API Gateway Lambda Authorizer with Request     |
| **APIGatewayProxyEventV2Model**             | Lambda Event Source payload for Amazon API Gateway v2 payload                         |
| **ApiGatewayAuthorizerRequestV2**           | Lambda Event Source payload for Amazon API Gateway v2 Lambda Authorizer               |
| **BedrockAgentEventModel**                  | Lambda Event Source payload for Bedrock Agents                                        |
| **CloudFormationCustomResourceCreateModel** | Lambda Event Source payload for AWS CloudFormation `CREATE` operation                 |
| **CloudFormationCustomResourceUpdateModel** | Lambda Event Source payload for AWS CloudFormation `UPDATE` operation                 |
| **CloudFormationCustomResourceDeleteModel** | Lambda Event Source payload for AWS CloudFormation `DELETE` operation                 |
| **CloudwatchLogsModel**                     | Lambda Event Source payload for Amazon CloudWatch Logs                                |
| **DynamoDBStreamModel**                     | Lambda Event Source payload for Amazon DynamoDB Streams                               |
| **EventBridgeModel**                        | Lambda Event Source payload for Amazon EventBridge                                    |
| **KafkaMskEventModel**                      | Lambda Event Source payload for AWS MSK payload                                       |
| **KafkaSelfManagedEventModel**              | Lambda Event Source payload for self managed Kafka payload                            |
| **KinesisDataStreamModel**                  | Lambda Event Source payload for Amazon Kinesis Data Streams                           |
| **KinesisFirehoseModel**                    | Lambda Event Source payload for Amazon Kinesis Firehose                               |
| **KinesisFirehoseSqsModel**                 | Lambda Event Source payload for SQS messages wrapped in Kinesis Firehose records      |
| **LambdaFunctionUrlModel**                  | Lambda Event Source payload for Lambda Function URL payload                           |
| **S3BatchOperationModel**                   | Lambda Event Source payload for Amazon S3 Batch Operation                             |
| **S3EventNotificationEventBridgeModel**     | Lambda Event Source payload for Amazon S3 Event Notification to EventBridge.          |
| **S3Model**                                 | Lambda Event Source payload for Amazon S3                                             |
| **S3ObjectLambdaEvent**                     | Lambda Event Source payload for Amazon S3 Object Lambda                               |
| **S3SqsEventNotificationModel**             | Lambda Event Source payload for S3 event notifications wrapped in SQS event (S3->SQS) |
| **SesModel**                                | Lambda Event Source payload for Amazon Simple Email Service                           |
| **SnsModel**                                | Lambda Event Source payload for Amazon Simple Notification Service                    |
| **SqsModel**                                | Lambda Event Source payload for Amazon SQS                                            |
| **VpcLatticeModel**                         | Lambda Event Source payload for Amazon VPC Lattice                                    |
| **VpcLatticeV2Model**                       | Lambda Event Source payload for Amazon VPC Lattice v2 payload                         |

#### Extending built-in models

You can extend them to include your own models, and yet have all other known fields parsed along the way.

???+ tip
    For Mypy users, we only allow type override for fields where payload is injected e.g. `detail`, `body`, etc.

**Example: custom data model with Amazon EventBridge**
Use the model to validate and extract relevant information from the incoming event. This can be useful when you need to handle events with a specific structure or when you want to ensure that the event data conforms to certain rules.

=== "Custom data model"

    ```python
    --8<-- "examples/parser/src/custom_data_model_with_eventbridge.py"
    ```

=== "Sample event"

    ```json
    --8<-- "examples/parser/src/data_model_eventbridge.json"
    ```


## Advanced

### Envelopes

Envelopes use JMESPath expressions to extract specific portions of complex, nested JSON structures. This feature simplifies processing events from various AWS services by allowing you to focus on core data without unnecessary metadata or wrapper information.

**Purpose of the Envelope**

- Data Extraction: The envelope helps extract the specific data we need from a larger, more complex event structure.
- Standardization: It allows us to handle different event sources in a consistent manner.
- Simplification: By using an envelope, we can focus on parsing only the relevant part of the event, ignoring the surrounding metadata.

Envelopes can be used via `envelope` parameter available in both `parse` function and `event_parser` decorator.

All you want is what's inside the `detail` key, from the payload in the sample example.

Using `@event_parser` decorator to automatically parse the EventBridge event and extract the UserModel data. The envelope, specifically `envelopes.EventBridgeEnvelope` in this case, is used to extract the relevant data from a complex event structure. It acts as a wrapper or container that holds additional metadata and the actual payload we're interested in.

=== "Envelopes using event parser decorator"

    ```python
    --8<-- "examples/parser/src/envelope_with_event_parser.py"
    ```

=== "Sample event"

    ```json
    --8<-- "examples/parser/src/envelope_payload.json"
    ```


#### Built-in envelopes

Parsers provides built-in envelopes to extract and parse specific parts of complex event structures. These envelopes simplify handling nested data in events from various AWS services, allowing you to focus on the relevant information for your Lambda function.

| Envelope name                 | Behaviour                                                                                                                                                                                             | Return                             |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| **DynamoDBStreamEnvelope**    | 1. Parses data using `DynamoDBStreamModel`. `` 2. Parses records in `NewImage` and `OldImage` keys using your model. `` 3. Returns a list with a dictionary containing `NewImage` and `OldImage` keys | `List[Dict[str, Optional[Model]]]` |
| **EventBridgeEnvelope**       | 1. Parses data using `EventBridgeModel`. ``2. Parses`detail` key using your model and returns it.                                                                                                     | `Model`                            |
| **SqsEnvelope**               | 1. Parses data using `SqsModel`. ``2. Parses records in`body` key using your model and return them in a list.                                                                                         | `List[Model]`                      |
| **CloudWatchLogsEnvelope**    | 1. Parses data using `CloudwatchLogsModel` which will base64 decode and decompress it. ``2. Parses records in`message` key using your model and return them in a list.                                | `List[Model]`                      |
| **KinesisDataStreamEnvelope** | 1. Parses data using `KinesisDataStreamModel` which will base64 decode it. ``2. Parses records in in`Records` key using your model and returns them in a list.                                        | `List[Model]`                      |
| **KinesisFirehoseEnvelope**   | 1. Parses data using `KinesisFirehoseModel` which will base64 decode it. ``2. Parses records in in`Records` key using your model and returns them in a list.                                          | `List[Model]`                      |
| **SnsEnvelope**               | 1. Parses data using `SnsModel`. ``2. Parses records in`body` key using your model and return them in a list.                                                                                         | `List[Model]`                      |
| **SnsSqsEnvelope**            | 1. Parses data using `SqsModel`. `` 2. Parses SNS records in `body` key using `SnsNotificationModel`. `` 3. Parses data in `Message` key using your model and return them in a list.                  | `List[Model]`                      |
| **ApiGatewayEnvelope**        | 1. Parses data using `APIGatewayProxyEventModel`. ``2. Parses`body` key using your model and returns it.                                                                                              | `Model`                            |
| **ApiGatewayV2Envelope**      | 1. Parses data using `APIGatewayProxyEventV2Model`. ``2. Parses`body` key using your model and returns it.                                                                                            | `Model`                            |
| **LambdaFunctionUrlEnvelope** | 1. Parses data using `LambdaFunctionUrlModel`. ``2. Parses`body` key using your model and returns it.                                                                                                 | `Model`                            |
| **KafkaEnvelope**             | 1. Parses data using `KafkaRecordModel`. ``2. Parses`value` key using your model and returns it.                                                                                                      | `Model`                            |
| **VpcLatticeEnvelope**        | 1. Parses data using `VpcLatticeModel`. ``2. Parses`value` key using your model and returns it.                                                                                                       | `Model`                            |
| **BedrockAgentEnvelope**      | 1. Parses data using `BedrockAgentEventModel`. ``2. Parses`inputText` key using your model and returns it.                                                                                            | `Model`                            |

#### Bringing your own envelope

You can create your own Envelope model and logic by inheriting from `BaseEnvelope`, and implementing the `parse` method.

Here's a snippet of how the EventBridge envelope we demonstrated previously is implemented.

=== "Bring your own envelope with Event Bridge"

    ```python
    --8<-- "examples/parser/src/bring_your_own_envelope.py"
    ```

=== "Sample event"

    ```json
    --8<-- "examples/parser/src/bring_your_own_envelope.json"
    ```


**What's going on here, you might ask**:

- **EventBridgeEnvelope**: extracts the detail field from EventBridge events.
- **OrderDetail Model**: defines and validates the structure of order data.
- **@event_parser**: decorator automates parsing and validation of incoming events using the specified model and envelope.

### Data model validation

???+ warning
    This is radically different from the **Validator utility** which validates events against JSON Schema.

You can use Pydantic's validator for deep inspection of object values and complex relationships.

There are two types of class method decorators you can use:

- **`field_validator`** - Useful to quickly validate an individual field and its value
- **`model_validator`** - Useful to validate the entire model's data

Keep the following in mind regardless of which decorator you end up using it:

- You must raise either `ValueError`, `TypeError`, or `AssertionError` when value is not compliant
- You must return the value(s) itself if compliant

#### Field Validator

Quick validation using decorator `field_validator` to verify whether the field `message` has the value of `hello world`.

```python title="field_validator.py"
--8<-- "examples/parser/src/field_validator.py"
```

If you run using a test event `{"message": "hello universe"}` you should expect the following error with the message we provided in our exception:

```python
  Message must be hello world! (type=value_error)
```

Alternatively, you can pass `'*'` as an argument for the decorator so that you can validate every value available.

```python title="field_validator_all_values.py"
--8<-- "examples/parser/src/field_validator_all_values.py"
```

Try with `event={"message": "hello universe", "sender": "universe"}` to get a validation error, as "sender" does not contain white spaces.

#### Model validator

`model_validator` can help when you have a complex validation mechanism. For example finding whether data has been omitted or comparing field values.

**Key points about model_validator:**

- It runs after all other validators have been called.
- It receives all the values of the model as a dictionary.
- It can modify or validate multiple fields at once.
- It's useful for validations that depend on multiple fields.

```python title="model_validator.py"
--8<-- "examples/parser/src/model_validator.py"
```

- The keyword argument `mode='after'` will cause the validator to be called after all field-level validation and parsing has been completed.

???+ info
    You can read more about validating list items, reusing validators, validating raw inputs, and a lot more in [Pydantic&#39;s documentation](`https://pydantic-docs.helpmanual.io/usage/validators/`).

**String fields that contain JSON data**

Wrap these fields with [Pydantic&#39;s Json Type](https://pydantic-docs.helpmanual.io/usage/types/#json-type){target="\_blank" rel="nofollow"}. This approach allows Pydantic to properly parse and validate the JSON content, ensuring type safety and data integrity.


=== "Validate string fields containing JSON data"

    ```python
    --8<-- "examples/parser/src/string_fields_contain_json.py"
    ```

=== "Sample event"

    ```json
    --8<-- "examples/parser/src/json_data_string.json"
    ```

Alternatively, you could use a [Pydantic validator](https://pydantic-docs.helpmanual.io/usage/validators/){target="\_blank" rel="nofollow"} to transform the JSON string into a dict before the mapping.

=== "Validate string fields containing JSON data using Pydantic validator"

    ```python
    --8<-- "examples/parser/src/string_fields_contain_json_pydantic_validator.py"
    ```

=== "Sample event"

    ```json
    --8<-- "examples/parser/src/json_data_string.json"
    ```


### Serialization

Models in Pydantic offer more than direct attribute access. They can be transformed, serialized, and exported in various formats.

Pydantic's definition of _serialization_ is broader than usual. It includes converting structured objects to simpler Python types, not just data to strings or bytes. This reflects the close relationship between these processes in Pydantic.

Read more at [Serialization for Pydantic documentation](https://docs.pydantic.dev/latest/concepts/serialization/#model_copy){target="\_blank" rel="nofollow"}.

```python title="serialization_parser.py"
--8<-- "examples/parser/src/serialization_parser.py"
```

???+ info
    There are number of advanced use cases well documented in Pydantic's doc such as creating [immutable models](https://pydantic-docs.helpmanual.io/usage/models/#faux-immutability){target="\_blank" rel="nofollow"}, [declaring fields with dynamic values](https://pydantic-docs.helpmanual.io/usage/models/#field-with-dynamic-default-value){target="\_blank" rel="nofollow"}.

## FAQ

**When should I use parser vs data_classes utility?**

Use data classes utility when you're after autocomplete, self-documented attributes and helpers to extract data from common event sources.

Parser is best suited for those looking for a trade-off between defining their models for deep validation, parsing and autocomplete for an additional dependency to be brought in.

**How do I import X from Pydantic?**

We export most common classes, exceptions, and utilities from Pydantic as part of parser e.g. `from aws_lambda_powertools.utilities.parser import BaseModel`.

If what you're trying to use isn't available as part of the high level import system, use the following escape _most_ hatch mechanism:

```python
from aws_lambda_powertools.utilities.parser.pydantic import <what you'd like to import'>
```
