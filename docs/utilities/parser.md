---
title: Parser
description: Utility
---

This utility provides data parsing and deep validation using [Pydantic](https://pydantic-docs.helpmanual.io/).

**Key features**

* Defines data in pure Python classes, then parse, validate and extract only what you want
* Built-in envelopes to unwrap, extend, and validate popular event sources payloads
* Enforces type hints at runtime with user-friendly errors

**Extra dependency**

!!! warning
    This will increase the overall package size by approximately 75MB due to Pydantic dependency.

Install parser's extra dependencies using **`pip install aws-lambda-powertools[pydantic]`**.

## Defining models

You can define models to parse incoming events by inheriting from `BaseModel`.

=== "hello_world_model.py"

    ```python
    from aws_lambda_powertools.utilities.parser import BaseModel
    from typing import List, Optional

    class OrderItem(BaseModel):
        id: int
        quantity: int
        description: str

    class Order(BaseModel):
        id: int
        description: str
        items: List[OrderItem] # nesting models are supported
        optional_field: Optional[str] # this field may or may not be available when parsing
    ```

These are simply Python classes that inherit from BaseModel. **Parser** enforces type hints declared in your model at runtime.

## Parsing events

You can parse inbound events using **event_parser** decorator, or the standalone `parse` function. Both are also able to parse either dictionary or JSON string as an input.

### event_parser decorator

Use the decorator for fail fast scenarios where you want your Lambda function to raise an exception in the event of a malformed payload.

`event_parser` decorator will throw a `ValidationError` if your event cannot be parsed according to the model.

> NOTE: **This decorator will replace the `event` object with the parsed model if successful**. This means you might be careful when nesting other decorators that expect `event` to be a `dict`.

=== "event_parser_decorator.py"

    ```python hl_lines="18"
    from aws_lambda_powertools.utilities.parser import event_parser, BaseModel, ValidationError
    from aws_lambda_powertools.utilities.typing import LambdaContext

    import json

    class OrderItem(BaseModel):
        id: int
        quantity: int
        description: str

    class Order(BaseModel):
        id: int
        description: str
        items: List[OrderItem] # nesting models are supported
        optional_field: Optional[str] # this field may or may not be available when parsing


    @event_parser(model=Order)
    def handler(event: Order, context: LambdaContext):
        print(event.id)
        print(event.description)
        print(event.items)

        order_items = [items for item in event.items]
        ...

    payload = {
        "id": 10876546789,
        "description": "My order",
        "items": [
            {
                "id": 1015938732,
                "quantity": 1,
                "description": "item xpto"
            }
        ]
    }

    handler(event=payload, context=LambdaContext())
    handler(event=json.dumps(payload), context=LambdaContext()) # also works if event is a JSON string
    ```

### parse function

Use this standalone function when you want more control over the data validation process, for example returning a 400 error for malformed payloads.

=== "parse_standalone_example.py"

    ```python hl_lines="21 30"
    from aws_lambda_powertools.utilities.parser import parse, BaseModel, ValidationError

    class OrderItem(BaseModel):
        id: int
        quantity: int
        description: str

    class Order(BaseModel):
        id: int
        description: str
        items: List[OrderItem] # nesting models are supported
        optional_field: Optional[str] # this field may or may not be available when parsing


    payload = {
        "id": 10876546789,
        "description": "My order",
        "items": [
            {
                # this will cause a validation error
                "id": [1015938732],
                "quantity": 1,
                "description": "item xpto"
            }
        ]
    }

    def my_function():
        try:
            parsed_payload: Order = parse(event=payload, model=Order)
            # payload dict is now parsed into our model
            return parsed_payload.items
        except ValidationError:
            return {
                "status_code": 400,
                "message": "Invalid order"
            }
    ```

## Built-in models

Parser comes with the following built-in models:

Model name | Description
------------------------------------------------- | ----------------------------------------------------------------------------------------------------------
**DynamoDBStreamModel** | Lambda Event Source payload for Amazon DynamoDB Streams
**EventBridgeModel** | Lambda Event Source payload for Amazon EventBridge
**SqsModel** | Lambda Event Source payload for Amazon SQS
**AlbModel** | Lambda Event Source payload for Amazon Application Load Balancer
**CloudwatchLogsModel** | Lambda Event Source payload for Amazon CloudWatch Logs
**S3Model** | Lambda Event Source payload for Amazon S3
**KinesisDataStreamModel** | Lambda Event Source payload for Amazon Kinesis Data Streams
**SesModel** |  Lambda Event Source payload for Amazon Simple Email Service
**SnsModel** |  Lambda Event Source payload for Amazon Simple Notification Service

### extending built-in models

You can extend them to include your own models, and yet have all other known fields parsed along the way.

**EventBridge example**

=== "extending_builtin_models.py"

    ```python hl_lines="16-17 28 41"
    from aws_lambda_powertools.utilities.parser import parse, BaseModel
    from aws_lambda_powertools.utilities.parser.models import EventBridgeModel

    from typing import List, Optional

    class OrderItem(BaseModel):
        id: int
        quantity: int
        description: str

    class Order(BaseModel):
        id: int
        description: str
        items: List[OrderItem]

    class OrderEventModel(EventBridgeModel):
        detail: Order

    payload = {
        "version": "0",
        "id": "6a7e8feb-b491-4cf7-a9f1-bf3703467718",
        "detail-type": "OrderPurchased",
        "source": "OrderService",
        "account": "111122223333",
        "time": "2020-10-22T18:43:48Z",
        "region": "us-west-1",
        "resources": ["some_additional"],
        "detail": {
            "id": 10876546789,
            "description": "My order",
            "items": [
                {
                    "id": 1015938732,
                    "quantity": 1,
                    "description": "item xpto"
                }
            ]
        }
    }

    ret = parse(model=OrderEventModel, event=payload)

    assert ret.source == "OrderService"
    assert ret.detail.description == "My order"
    assert ret.detail_type == "OrderPurchased" # we rename it to snake_case since detail-type is an invalid name

    for order_item in ret.detail.items:
        ...
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

=== "parse_eventbridge_payload.py"

    ```python hl_lines="18-22 25 31"
    from aws_lambda_powertools.utilities.parser import event_parser, parse, BaseModel, envelopes
    from aws_lambda_powertools.utilities.typing import LambdaContext

    class UserModel(BaseModel):
        username: str
        password1: str
        password2: str

    payload = {
        "version": "0",
        "id": "6a7e8feb-b491-4cf7-a9f1-bf3703467718",
        "detail-type": "CustomerSignedUp",
        "source": "CustomerService",
        "account": "111122223333",
        "time": "2020-10-22T18:43:48Z",
        "region": "us-west-1",
        "resources": ["some_additional_"],
        "detail": {
            "username": "universe",
            "password1": "myp@ssword",
            "password2": "repeat password"
        }
    }

    ret = parse(model=UserModel, envelope=envelopes.EventBridgeModel, event=payload)

    # Parsed model only contains our actual model, not the entire EventBridge + Payload parsed
    assert ret.password1 == ret.password2

    # Same behaviour but using our decorator
    @event_parser(model=UserModel, envelope=envelopes.EventBridgeModel)
    def handler(event: UserModel, context: LambdaContext):
        assert event.password1 == event.password2
    ```

**What's going on here, you might ask**:

1. We imported built-in `envelopes` from the parser utility
2. Used `envelopes.EventBridgeModel` as the envelope for our `UserModel` model
3. Parser parsed the original event against the EventBridge model
4. Parser then parsed the `detail` key using `UserModel`


### built-in envelopes

Parser comes with the following built-in envelopes, where `Model` in the return section is your given model.

Envelope name | Behaviour | Return
------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------
**DynamoDBStreamEnvelope** | 1. Parses data using `DynamoDBStreamModel`. <br/> 2. Parses records in `NewImage` and `OldImage` keys using your model. <br/> 3. Returns a list with a dictionary containing `NewImage` and `OldImage` keys | `List[Dict[str, Optional[Model]]]`
**EventBridgeEnvelope** | 1. Parses data using `EventBridgeModel`. <br/> 2. Parses `detail` key using your model and returns it. | `Model`
**SqsEnvelope** | 1. Parses data using `SqsModel`. <br/> 2. Parses records in `body` key using your model and return them in a list. | `List[Model]`
**CloudWatchLogsEnvelope** | 1. Parses data using `CloudwatchLogsModel` which will base64 decode and decompress it. <br/> 2. Parses records in `message` key using your model and return them in a list. | `List[Model]`
**KinesisDataStreamEnvelope** | 1. Parses data using `KinesisDataStreamModel` which will base64 decode it. <br/> 2. Parses records in in `Records` key using your model and returns them in a list. | `List[Model]`
**SnsEnvelope** | 1. Parses data using `SnsModel`. <br/> 2. Parses records in `body` key using your model and return them in a list. | `List[Model]`
**SnsSqsEnvelope** | 1. Parses data using `SqsModel`. <br/> 2. Parses SNS records in `body` key using `SnsNotificationModel`. <br/> 3. Parses data in `Message` key using your model and return them in a list. | `List[Model]`

### bringing your own envelope

You can create your own Envelope model and logic by inheriting from `BaseEnvelope`, and implementing the `parse` method.

Here's a snippet of how the EventBridge envelope we demonstrated previously is implemented.

**EventBridge Model**

=== "eventbridge_model.py"

    ```python
    from datetime import datetime
    from typing import Any, Dict, List

    from aws_lambda_powertools.utilities.parser import BaseModel, Field


    class EventBridgeModel(BaseModel):
        version: str
        id: str  # noqa: A003,VNE003
        source: str
        account: str
        time: datetime
        region: str
        resources: List[str]
        detail_type: str = Field(None, alias="detail-type")
        detail: Dict[str, Any]
    ```

**EventBridge Envelope**

=== "eventbridge_envelope.py"

    ```python hl_lines="8 10 25 26"
    from aws_lambda_powertools.utilities.parser import BaseEnvelope, models
    from aws_lambda_powertools.utilities.parser.models import EventBridgeModel

    from typing import Any, Dict, Optional, TypeVar

    Model = TypeVar("Model", bound=BaseModel)

    class EventBridgeEnvelope(BaseEnvelope):

        def parse(self, data: Optional[Union[Dict[str, Any], Any]], model: Model) -> Optional[Model]:
            """Parses data found with model provided

            Parameters
            ----------
            data : Dict
                Lambda event to be parsed
            model : Model
                Data model provided to parse after extracting data using envelope

            Returns
            -------
            Any
                Parsed detail payload with model provided
            """
            parsed_envelope = EventBridgeModel.parse_obj(data)
            return self._parse(data=parsed_envelope.detail, model=model)
    ```

**What's going on here, you might ask**:

1. We defined an envelope named `EventBridgeEnvelope` inheriting from `BaseEnvelope`
2. Implemented the `parse` abstract method taking `data` and `model` as parameters
3. Then, we parsed the incoming data with our envelope to confirm it matches EventBridge's structure defined in `EventBridgeModel`
4. Lastly, we call `_parse` from `BaseEnvelope` to parse the data in our envelope (.detail) using the customer model

## Data model validation

!!! warning
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

=== "deep_data_validation.py"

    ```python hl_lines="6"
    from aws_lambda_powertools.utilities.parser import parse, BaseModel, validator

    class HelloWorldModel(BaseModel):
        message: str

        @validator('message')
        def is_hello_world(cls, v):
            if v != "hello world":
                raise ValueError("Message must be hello world!")
            return v

    parse(model=HelloWorldModel, event={"message": "hello universe"})
    ```

If you run as-is, you should expect the following error with the message we provided in our exception:

```
message
  Message must be hello world! (type=value_error)
```

Alternatively, you can pass `'*'` as an argument for the decorator so that you can validate every value available.

=== "validate_all_field_values.py"

    ```python hl_lines="7"
    from aws_lambda_powertools.utilities.parser import parse, BaseModel, validator

    class HelloWorldModel(BaseModel):
        message: str
        sender: str

        @validator('*')
        def has_whitespace(cls, v):
            if ' ' not in v:
                raise ValueError("Must have whitespace...")

            return v

    parse(model=HelloWorldModel, event={"message": "hello universe", "sender": "universe"})
    ```

### validating entire model

`root_validator` can help when you have a complex validation mechanism. For example finding whether data has been omitted, comparing field values, etc.

=== "validate_all_field_values.py"

    ```python
    from aws_lambda_powertools.utilities.parser import parse, BaseModel, validator

    class UserModel(BaseModel):
        username: str
        password1: str
        password2: str

        @root_validator
        def check_passwords_match(cls, values):
            pw1, pw2 = values.get('password1'), values.get('password2')
            if pw1 is not None and pw2 is not None and pw1 != pw2:
                raise ValueError('passwords do not match')
            return values

    payload = {
        "username": "universe",
        "password1": "myp@ssword",
        "password2": "repeat password"
    }

    parse(model=UserModel, event=payload)
    ```

!!! info
    You can read more about validating list items, reusing validators, validating raw inputs, and a lot more in <a href="https://pydantic-docs.helpmanual.io/usage/validators/">Pydantic's documentation</a>.


## Advanced use cases

!!! info
    **Looking to auto-generate models from JSON, YAML, JSON Schemas, OpenApi, etc?**

    Use Koudai Aono's [data model code generation tool for Pydantic](https://github.com/koxudaxi/datamodel-code-generator)

There are number of advanced use cases well documented in Pydantic's doc such as creating [immutable models](https://pydantic-docs.helpmanual.io/usage/models/#faux-immutability), [declaring fields with dynamic values](https://pydantic-docs.helpmanual.io/usage/models/#field-with-dynamic-default-value)) e.g. UUID, and [helper functions to parse models from files, str](https://pydantic-docs.helpmanual.io/usage/models/#helper-functions), etc.

Two possible unknown use cases are Models and exception' serialization. Models have methods to [export them](https://pydantic-docs.helpmanual.io/usage/exporting_models/) as `dict`, `JSON`, `JSON Schema`, and Validation exceptions can be exported as JSON.

=== "serializing_models_exceptions.py"

    ```python hl_lines="21 28-31"
    from aws_lambda_powertools.utilities import Logger
    from aws_lambda_powertools.utilities.parser import parse, BaseModel, ValidationError, validator

    logger = Logger(service="user")

    class UserModel(BaseModel):
        username: str
        password1: str
        password2: str

    payload = {
        "username": "universe",
        "password1": "myp@ssword",
        "password2": "repeat password"
    }

    def my_function():
        try:
            return parse(model=UserModel, event=payload)
        except ValidationError as e:
            logger.exception(e.json())
            return {
                "status_code": 400,
                "message": "Invalid username"
            }

    User: UserModel = my_function()
    user_dict = User.dict()
    user_json = User.json()
    user_json_schema_as_dict = User.schema()
    user_json_schema_as_json = User.schema_json(indent=2)
    ```

These can be quite useful when manipulating models that later need to be serialized as inputs for services like DynamoDB, EventBridge, etc.

## FAQ

**When should I use parser vs data_classes utility?**

Use data classes utility when you're after autocomplete, self-documented attributes and helpers to extract data from common event sources.

Parser is best suited for those looking for a trade-off between defining their models for deep validation, parsing and autocomplete for an additional dependency to be brought in.

**How do I import X from Pydantic?**

We export most common classes, exceptions, and utilities from Pydantic as part of parser e.g. `from aws_lambda_powertools.utilities.parser import BaseModel`.

If what's your trying to use isn't available as part of the high level import system, use the following escape hatch mechanism:

=== "escape_hatch.py"

    ```python
    from aws_lambda_powertools.utilities.parser.pydantic import <what you'd like to import'>
    ```

**What is the cold start impact in bringing this additional dependency?**

No significant cold start impact. It does increase the final uncompressed package by **71M**, when you bring the additional dependency that parser requires.

Artillery load test sample against a [hello world sample](https://github.com/aws-samples/cookiecutter-aws-sam-python) using Tracer, Metrics, and Logger with and without parser.

**No parser**

> **Uncompressed package size**: 55M, **p99**: 180.3ms

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

> **Uncompressed package size**: 128M, **p99**: 193.1ms

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
