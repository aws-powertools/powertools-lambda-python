from datetime import datetime
from typing import Dict, List, Optional
from typing import Type as TypingType
from typing import Union

from aws_lambda_powertools.utilities.parser.types import Literal
from pydantic import BaseModel, root_validator
from pydantic.networks import HttpUrl


class SnsMsgAttributeModel(BaseModel):
    Type: str
    Value: str


class SnsNotificationModel(BaseModel):
    Subject: Optional[str]
    TopicArn: str
    UnsubscribeUrl: Optional[HttpUrl]
    Type: Literal["Notification"]
    MessageAttributes: Optional[Dict[str, SnsMsgAttributeModel]]
    Message: Union[str, TypingType[BaseModel]]
    MessageId: str
    SigningCertUrl: Optional[HttpUrl]
    Signature: Optional[str]
    Timestamp: datetime
    SignatureVersion: Optional[str]

    @root_validator(pre=True, allow_reuse=True)
    def check_sqs_protocol(cls, values):
        sqs_rewritten_keys = ("UnsubscribeURL", "SigningCertURL")
        for k in sqs_rewritten_keys:
            if k in values:
                values[k] = values.pop(k)
        return values


class SnsRecordModel(BaseModel):
    EventSource: Literal["aws:sns"]
    EventVersion: str
    EventSubscriptionArn: str
    Sns: SnsNotificationModel


class SnsModel(BaseModel):
    Records: List[SnsRecordModel]
