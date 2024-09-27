---
title: Parser (Pydantic)
description: Utility
---

<!-- markdownlint-disable MD043 -->

The Parser utility in Powertools for AWS Lambda simplifies data parsing and validation using [Pydantic](https://pydantic-docs.helpmanual.io/){target="\_blank" rel="nofollow"}. It allows you to define data models in pure Python classes, parse and validate incoming events, and extract only the data you need.

## Key features

- Define data models using Python classes
- Parse and validate Lambda event payloads
- Built-in support for common AWS event sources
- Runtime type checking with user-friendly error messages
- Compatible with Pydantic v2

## Getting started

### Install

Powertools for AWS Lambda (Python) supports Pydantic v2. Each Pydantic version requires different dependencies before you can use Parser.

!!! info "This is not necessary if you're installing Powertools for AWS Lambda (Python) via [Lambda Layer/SAR](../index.md#lambda-layer){target="\_blank"}"

???+ warning
    This will increase the compressed package size by >10MB due to the Pydantic dependency.

    To reduce the impact on the package size at the expense of 30%-50% of its performance[Pydantic can also be
    installed without binary files](https://pydantic-docs.helpmanual.io/install/#performance-vs-package-size-trade-off){target="_blank" rel="nofollow"}:

    Pip example:`SKIP_CYTHON=1 pip install --no-binary pydantic aws-lambda-powertools[parser]`

```python
pip install aws-lambda-powertools
```

You can also add as a dependency in your preferred tool: e.g., requirements.txt, pyproject.toml.

### Data Model with Parse

Define models by inheriting from `BaseModel` to parse incoming events. Pydantic then validates the data, ensuring all fields adhere to specified types and guaranteeing data integrity.

#### Event parser

The `event_parser` decorator automatically parses and validates the event.

```python
from aws_lambda_powertools.utilities.parser import BaseModel, event_parser, ValidationError

class MyEvent(BaseModel):
    id: int
    name: str

@event_parser(model=MyEvent)
def lambda_handler(event: MyEvent, context):
    try:
        return {"statusCode": 200, "body": f"Hello {event.name}, your ID is {event.id}"}
    except ValidationError as e:
        return {"statusCode": 400, "body": f"Invalid input: {str(e)}"}
```

The `@event_parser(model=MyEvent)` automatically parses the event into the specified Pydantic model MyEvent.

The function catches **ValidationError**, returning a 400 status code with an error message if the input doesn't match the `MyEvent` model. It provides robust error handling for invalid inputs.

#### Parse function

The `parse()` function allows you to manually control when and how an event is parsed into a Pydantic model. This can be useful in cases where you need flexibility, such as handling different event formats or adding custom logic before parsing.

```python
from aws_lambda_powertools.utilities.parser import BaseModel, parse, ValidationError

# Define a Pydantic model for the expected structure of the input
class MyEvent(BaseModel):
    id: int
    name: str

def lambda_handler(event: dict, context):
    try:
        # Manually parse the incoming event into MyEvent model
        parsed_event: MyEvent = parse(model=MyEvent, event=event)
        return {
            "statusCode": 200,
            "body": f"Hello {parsed_event.name}, your ID is {parsed_event.id}"
        }
    except ValidationError as e:
        # Catch validation errors and return a 400 response
        return {
            "statusCode": 400,
            "body": f"Validation error: {str(e)}"
        }

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

```python
from aws_lambda_powertools.utilities.parser import BaseModel, parse, Field
from aws_lambda_powertools.utilities.parser.models import EventBridgeModel

# Define a custom EventBridge model by extending the built-in EventBridgeModel
class MyCustomEventBridgeModel(EventBridgeModel):
    detail_type: str = Field(alias="detail-type")
    source: str
    detail: dict

def lambda_handler(event: dict, context):
    try:
        # Manually parse the incoming event into the custom model
        parsed_event: MyCustomEventBridgeModel = parse(model=MyCustomEventBridgeModel, event=event)

        return {
            "statusCode": 200,
            "body": f"Event from {parsed_event.source}, type: {parsed_event.detail_type}"
        }
    except ValidationError as e:
        return {
            "statusCode": 400,
            "body": f"Validation error: {str(e)}"
        }

```

You can simulate an EventBridge event like the following to test the Lambda function:

**Sample event:**

```json
{
  "version": "0",
  "id": "abcd-1234-efgh-5678",
  "detail-type": "order.created",
  "source": "my.order.service",
  "account": "123456789012",
  "time": "2023-09-10T12:00:00Z",
  "region": "us-west-2",
  "resources": [],
  "detail": {
    "orderId": "O-12345",
    "amount": 100.0
  }
}
```

## Advanced

### Envelopes

Envelopes use JMESPath expressions to extract specific portions of complex, nested JSON structures. This feature simplifies processing events from various AWS services by allowing you to focus on core data without unnecessary metadata or wrapper information.

**Purpose of the Envelope**

- Data Extraction: The envelope helps extract the specific data we need from a larger, more complex event structure.
- Standardization: It allows us to handle different event sources in a consistent manner.
- Simplification: By using an envelope, we can focus on parsing only the relevant part of the event, ignoring the surrounding metadata.

Envelopes can be used via `envelope` parameter available in both `parse` function and `event_parser` decorator.

Here's an example of parsing a model found in an event coming from EventBridge, where all you want is what's inside the `detail` key, from the payload below:

```json
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
            "parentid_1": "12345",
            "parentid_2": "6789"
        }
    }
```

An example using `@event_parser` decorator to automatically parse the EventBridge event and extract the UserModel data. The envelope, specifically `envelopes.EventBridgeEnvelope` in this case, is used to extract the relevant data from a complex event structure. It acts as a wrapper or container that holds additional metadata and the actual payload we're interested in.

```python
from aws_lambda_powertools.utilities.parser import event_parser, parse, BaseModel, envelopes
from aws_lambda_powertools.utilities.typing import LambdaContext

class UserModel(BaseModel):
   username: str
   parentid_1: str
   parentid_2: str

@event_parser(model=UserModel, envelope=envelopes.EventBridgeEnvelope)
def lambda_handler(event: UserModel, context: LambdaContext):
    if event.parentid_1!= event.parentid_2:
        return {
            "statusCode": 400,
            "body": "Parent ids do not match"
        }

    # If parentids match, proceed with user registration
    # Add your user registration logic here

    return {
        "statusCode": 200,
        "body": f"User {event.username} registered successfully"
    }
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

```python
import json
from typing import Any, Dict, Optional, TypeVar, Union
from aws_lambda_powertools.utilities.parser import BaseEnvelope, event_parser, BaseModel
from aws_lambda_powertools.utilities.parser.models import EventBridgeModel
from aws_lambda_powertools.utilities.typing import LambdaContext

Model = TypeVar("Model", bound=BaseModel)

class EventBridgeEnvelope(BaseEnvelope):
    def parse(self, data: Optional[Union[Dict[str, Any], Any]], model: type[Model]) -> Optional[Model]:
        if data is None:
            return None

        parsed_envelope = EventBridgeModel.parse_obj(data)
        return self._parse(data=parsed_envelope.detail, model=model)

class OrderDetail(BaseModel):
    order_id: str
    amount: float
    customer_id: str

@event_parser(model=OrderDetail, envelope=EventBridgeEnvelope)
def lambda_handler(event: OrderDetail, context: LambdaContext):
    try:
        # Process the order
        print(f"Processing order {event.order_id} for customer {event.customer_id}")
        print(f"Order amount: ${event.amount:.2f}")

        # Your business logic here
        # For example, you might save the order to a database or trigger a payment process

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Order {event.order_id} processed successfully",
                "order_id": event.order_id,
                "amount": event.amount,
                "customer_id": event.customer_id
            })
        }
    except Exception as e:
        print(f"Error processing order: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
```

You can use the following test event:

```json
{
  "version": "0",
  "id": "12345678-1234-1234-1234-123456789012",
  "detail-type": "Order Placed",
  "source": "com.mycompany.orders",
  "account": "123456789012",
  "time": "2023-05-03T12:00:00Z",
  "region": "us-west-2",
  "resources": [],
  "detail": {
    "order_id": "ORD-12345",
    "amount": 99.99,
    "customer_id": "CUST-6789"
  }
}
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

```python
from aws_lambda_powertools.utilities.parser import parse, BaseModel, field_validator
from aws_lambda_powertools.utilities.typing import LambdaContext

class HelloWorldModel(BaseModel):
    message: str

    @field_validator('message')
    def is_hello_world(cls, v):
        if v != "hello world":
            raise ValueError("Message must be hello world!")
        return v

def lambda_handler(event: dict, context: LambdaContext):
    try:
        parsed_event = parse(model=HelloWorldModel, event=event)
        return {
            "statusCode": 200,
            "body": f"Received message: {parsed_event.message}"
        }
    except ValueError as e:
        return {
            "statusCode": 400,
            "body": str(e)
        }

```

If you run using a test event `{"message": "hello universe"}` you should expect the following error with the message we provided in our exception:

```python
message
  Message must be hello world! (type=value_error)
```

Alternatively, you can pass `'*'` as an argument for the decorator so that you can validate every value available.

```python
from aws_lambda_powertools.utilities.parser import parse, BaseModel, field_validator
from aws_lambda_powertools.utilities.typing import LambdaContext

class HelloWorldModel(BaseModel):
    message: str
    sender: str

    @field_validator('*')
    def has_whitespace(cls, v):
        if ' ' not in v:
            raise ValueError("Must have whitespace...")
        return v

def lambda_handler(event: dict, context: LambdaContext):
    try:
        parsed_event = parse(model=HelloWorldModel, event=event)
        return {
            "statusCode": 200,
            "body": f"Received message: {parsed_event.message}"
        }
    except ValueError as e:
        return {
            "statusCode": 400,
            "body": str(e)
        }

```

Try with `event={"message": "hello universe", "sender": "universe"}` to get a validation error, as "sender" does not contain white spaces.

#### Model validator

`model_validator` can help when you have a complex validation mechanism. For example finding whether data has been omitted or comparing field values.

**Key points about model_validator:**

- It runs after all other validators have been called.
- It receives all the values of the model as a dictionary.
- It can modify or validate multiple fields at once.
- It's useful for validations that depend on multiple fields.

```python
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import parse, BaseModel, root_validator

class UserModel(BaseModel):
	username: str
	parentid_1: str
	parentid_2: str

	@model_validator(mode='after')
	def check_parents_match(cls, values):
		pi1, pi2 = values.get('parentid_1'), values.get('parentid_2')
		if pi1 is not None and pi2 is not None and pi1 != pi2:
			raise ValueError('Parent ids do not match')
		return values
def lambda_handler(event: dict, context: LambdaContext):
    try:
        parsed_event = parse(model=UserModel, event=event)
        return {
            "statusCode": 200,
            "body": f"Received parent id from: {parsed_event.username}"
        }
    except ValueError as e:
        return {
            "statusCode": 400,
            "body": str(e)
        }

```

- The keyword argument `mode='after'` will cause the validator to be called after all field-level validation and parsing has been completed.

???+ info
You can read more about validating list items, reusing validators, validating raw inputs, and a lot more in [Pydantic&#39;s documentation](`https://pydantic-docs.helpmanual.io/usage/validators/`).

**String fields that contain JSON data**

Wrap these fields with [Pydantic&#39;s Json Type](https://pydantic-docs.helpmanual.io/usage/types/#json-type){target="\_blank" rel="nofollow"}. This approach allows Pydantic to properly parse and validate the JSON content, ensuring type safety and data integrity.

```python
from typing import Any, Type
from aws_lambda_powertools.utilities.parser import event_parser, BaseEnvelope, BaseModel
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser.types import Json

class CancelOrder(BaseModel):
    order_id: int
    reason: str

class CancelOrderModel(BaseModel):
    body: Json[CancelOrder]

class CustomEnvelope(BaseEnvelope):
    def parse(self, data: dict, model: Type[BaseModel]) -> Any:
        return model.parse_obj({"body": data.get("body", {})})

@event_parser(model=CancelOrderModel, envelope=CustomEnvelope)
def lambda_handler(event: CancelOrderModel, context: LambdaContext):
    cancel_order: CancelOrder = event.body

    assert cancel_order.order_id is not None

    # Process the cancel order request
    print(f"Cancelling order {cancel_order.order_id} for reason: {cancel_order.reason}")

    return {
        "statusCode": 200,
        "body": f"Order {cancel_order.order_id} cancelled successfully"
    }
```

Alternatively, you could use a [Pydantic validator](https://pydantic-docs.helpmanual.io/usage/validators/){target="\_blank" rel="nofollow"} to transform the JSON string into a dict before the mapping.

```python
import json
from typing import Any, Type
from aws_lambda_powertools.utilities.parser import event_parser, BaseEnvelope, BaseModel, validator
from aws_lambda_powertools.utilities.typing import LambdaContext

class CancelOrder(BaseModel):
    order_id: int
    reason: str

class CancelOrderModel(BaseModel):
    body: CancelOrder

    @validator("body", pre=True)
    def transform_body_to_dict(cls, value):
        if isinstance(value, str):
            return json.loads(value)
        return value

class CustomEnvelope(BaseEnvelope):
    def parse(self, data: dict, model: Type[BaseModel]) -> Any:
        return model.parse_obj({"body": data.get("body", {})})

@event_parser(model=CancelOrderModel, envelope=CustomEnvelope)
def lambda_handler(event: CancelOrderModel, context: LambdaContext):
    cancel_order: CancelOrder = event.body

    assert cancel_order.order_id is not None

    # Process the cancel order request
    print(f"Cancelling order {cancel_order.order_id} for reason: {cancel_order.reason}")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": f"Order {cancel_order.order_id} cancelled successfully"})
    }

```

To test both examples above, you can use:

```json
{
  "body": "{\"order_id\": 12345, \"reason\": \"Changed my mind\"}"
}
```

### Serialization

Models in Pydantic offer more than direct attribute access. They can be transformed, serialized, and exported in various formats.

Pydantic's definition of _serialization_ is broader than usual. It includes converting structured objects to simpler Python types, not just data to strings or bytes. This reflects the close relationship between these processes in Pydantic.

Read more at [Serialization for Pydantic documentation](https://docs.pydantic.dev/latest/concepts/serialization/#model_copy){target="\_blank" rel="nofollow"}.

```python
from aws_lambda_powertools.utilities.parser import parse, BaseModel
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

class UserModel(BaseModel):
    username: str
    parentid_1: str
    parentid_2: str

def validate_user(event):
    try:
        user = parse(model=UserModel, event=event)
        return {
            "statusCode": 200,
            "body": user.model_dump_json()
        }
    except Exception as e:
        logger.exception("Validation error")
        return {
            "statusCode": 400,
            "body": str(e)
        }

@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info("Received event", extra={"event": event})

    result = validate_user(event)

    if result["statusCode"] == 200:
        user = UserModel.model_validate_json(result["body"])
        logger.info("User validated successfully", extra={"username": user.username})

        # Example of serialization
        user_dict = user.model_dump()
        user_json = user.model_dump_json()

        logger.debug("User serializations", extra={
            "dict": user_dict,
            "json": user_json
        })

    return result
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
