from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, root_validator
from pydantic.networks import HttpUrl

from aws_lambda_powertools.utilities.parser.types import Literal, Model


class SnsMsgAttributeModel(BaseModel):
    Type: str
    Value: str


class SnsNotificationModel(BaseModel):
    Subject: Optional[str]
    TopicArn: str
    UnsubscribeUrl: HttpUrl
    Type: Literal["Notification"]
    MessageAttributes: Optional[Dict[str, SnsMsgAttributeModel]]
    Message: Union[str, Model]
    MessageId: str
    SigningCertUrl: HttpUrl
    Signature: str
    Timestamp: datetime
    SignatureVersion: str

    @root_validator(pre=True, allow_reuse=True)
    def check_sqs_protocol(cls, values):
        sqs_rewritten_keys = ("UnsubscribeURL", "SigningCertURL")
        if any(key in sqs_rewritten_keys for key in values):
            values["UnsubscribeUrl"] = values.pop("UnsubscribeURL")
            values["SigningCertUrl"] = values.pop("SigningCertURL")
        return values


class SnsRecordModel(BaseModel):
    EventSource: Literal["aws:sns"]
    EventVersion: str
    EventSubscriptionArn: str
    Sns: SnsNotificationModel


class SnsModel(BaseModel):
    Records: List[SnsRecordModel]
