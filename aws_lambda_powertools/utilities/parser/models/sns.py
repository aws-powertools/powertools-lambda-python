from datetime import datetime
from typing import Dict, List, Literal, Optional, Union
from typing import Type as TypingType

from pydantic import BaseModel, Field, model_validator
from pydantic.networks import HttpUrl


class SnsMsgAttributeModel(BaseModel):
    Type: str = Field(
        description="The data type of the message attribute (String, Number, Binary, or custom data type).",
        examples=["String", "Number", "Binary", "String.Array", "Number.Array"],
    )
    Value: str = Field(
        description="The value of the message attribute. All values are strings, even for Number types.",
        examples=["TestString", "123", "TestBinary", '["item1", "item2"]'],
    )


class SnsNotificationModel(BaseModel):
    Subject: Optional[str] = Field(
        default=None,
        description="The subject parameter provided when the notification was published to the topic.",
        examples=["TestInvoke", "Alert: System maintenance", "Order Confirmation", None],
    )
    TopicArn: str = Field(
        description="The Amazon Resource Name (ARN) for the topic that this message was published to.",
        examples=[
            "arn:aws:sns:us-east-2:123456789012:sns-lambda",
            "arn:aws:sns:eu-west-1:123456789012:notification-topic",
            "arn:aws:sns:us-west-2:123456789012:alerts.fifo",
        ],
    )
    UnsubscribeUrl: HttpUrl = Field(
        description="A URL that you can use to unsubscribe the endpoint from this topic.",
        examples=[
            (
                "https://sns.us-east-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn= \
                arn:aws:sns:us-east-2:123456789012:test-lambda:21be56ed-a058-49f5-8c98-aedd2564c486"
            ),
            (
                "https://sns.eu-west-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn= \
                arn:aws:sns:eu-west-1:123456789012:notification-topic:abcd1234-5678-90ef-ghij-klmnopqrstuv"
            ),
        ],
    )
    Type: Literal["Notification"] = Field(
        description="The type of message. For Lambda triggers, this is always 'Notification'.",
        examples=["Notification"],
    )
    MessageAttributes: Optional[Dict[str, SnsMsgAttributeModel]] = Field(
        default=None,
        description="User-defined message attributes as key-value pairs with type information.",
        examples=[
            {"Test": {"Type": "String", "Value": "TestString"}},
            {"priority": {"Type": "Number", "Value": "1"}, "env": {"Type": "String", "Value": "prod"}},
            None,
        ],
    )
    Message: Union[str, TypingType[BaseModel]] = Field(
        description="The message value specified when the notification was published to the topic.",
        examples=[
            "Hello from SNS!",
            '{"alert": "CPU usage above 80%", "instance": "i-1234567890abcdef0"}',
            '{"order_id": 12345, "status": "confirmed", "total": 99.99}',
        ],
    )
    MessageId: str = Field(
        description="A Universally Unique Identifier, unique for each message published.",
        examples=[
            "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
            "da41e39f-ea4d-435a-b922-c6aae3915ebe",
            "f3c8d4e2-1a2b-4c5d-9e8f-7g6h5i4j3k2l",
        ],
    )
    SigningCertUrl: Optional[HttpUrl] = Field(
        default=None,
        description=(
            "The URL to the certificate that was used to sign the message. "
            "Not present for FIFO topics with content-based deduplication."
        ),
        examples=[
            "https://sns.us-east-2.amazonaws.com/SimpleNotificationService-1234567890.pem",
            "https://sns.eu-west-1.amazonaws.com/SimpleNotificationService-0987654321.pem",
            None,
        ],
    )  # NOTE: FIFO opt-in removes attribute
    Signature: Optional[str] = Field(
        default=None,
        description=(
            "Base64-encoded SHA1withRSA signature of the message. "
            "Not present for FIFO topics with content-based deduplication."
        ),
        examples=[
            "tcc6faL2yUC6dgZdmrwh1Y4cGa/ebXEkAi6RibDsvpi+tE/1+82j...65r==",
            "EXAMPLEw6JRNwm1LFQL4ICB0bnXrdB8ClRMTQFPGBfHs...EXAMPLEw==",
            None,
        ],
    )  # NOTE: FIFO opt-in removes attribute
    Timestamp: datetime = Field(
        description="The time (GMT) when the notification was published.",
        examples=[
            "2019-01-02T12:45:07.000Z",
            "2023-06-15T10:30:00.000Z",
            "2023-12-25T18:45:30.123Z",
        ],
    )
    SignatureVersion: Optional[str] = Field(
        default=None,
        description=(
            "Version of the Amazon SNS signature used. Not present for FIFO topics with content-based deduplication."
        ),
        examples=["1", "2", None],
    )  # NOTE: FIFO opt-in removes attribute

    @model_validator(mode="before")
    def check_sqs_protocol(cls, values):
        sqs_rewritten_keys = ("UnsubscribeURL", "SigningCertURL")
        if any(key in sqs_rewritten_keys for key in values):
            # The sentinel value 'None' forces the validator to fail with
            # ValidatorError instead of KeyError when the key is missing from
            # the SQS payload
            values["UnsubscribeUrl"] = values.pop("UnsubscribeURL", None)
            values["SigningCertUrl"] = values.pop("SigningCertURL", None)
        return values


class SnsRecordModel(BaseModel):
    EventSource: Literal["aws:sns"] = Field(
        description="The AWS service that invoked the function.",
        examples=["aws:sns"],
    )
    EventVersion: str = Field(
        description="The version of the event schema.",
        examples=["1.0", "2.0"],
    )
    EventSubscriptionArn: str = Field(
        description="The Amazon Resource Name (ARN) of the subscription.",
        examples=[
            "arn:aws:sns:us-east-2:123456789012:sns-lambda:21be56ed-a058-49f5-8c98-aedd2564c486",
            "arn:aws:sns:eu-west-1:123456789012:notification-topic:abcd1234-5678-90ef-ghij-klmnopqrstuv",
        ],
    )
    Sns: SnsNotificationModel = Field(
        description="The SNS message that triggered the Lambda function.",
    )


class SnsModel(BaseModel):
    Records: List[SnsRecordModel] = Field(
        description="A list of SNS message records included in the event.",
        examples=[[{"EventSource": "aws:sns", "Sns": {"MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e"}}]],
    )
