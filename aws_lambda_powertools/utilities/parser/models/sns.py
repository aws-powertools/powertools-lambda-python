from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import Literal

from pydantic import BaseModel, model_validator
from pydantic.networks import HttpUrl  # noqa: TCH002


class SnsMsgAttributeModel(BaseModel):
    Type: str
    Value: str


class SnsNotificationModel(BaseModel):
    Subject: str | None = None
    TopicArn: str
    UnsubscribeUrl: HttpUrl
    Type: Literal["Notification"]
    MessageAttributes: dict[str, SnsMsgAttributeModel] | None = None
    Message: str | type[BaseModel]
    MessageId: str
    SigningCertUrl: HttpUrl | None = None  # NOTE: FIFO opt-in removes attribute
    Signature: str | None = None  # NOTE: FIFO opt-in removes attribute
    Timestamp: datetime
    SignatureVersion: str | None = None  # NOTE: FIFO opt-in removes attribute

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
    EventSource: Literal["aws:sns"]
    EventVersion: str
    EventSubscriptionArn: str
    Sns: SnsNotificationModel


class SnsModel(BaseModel):
    Records: list[SnsRecordModel]
