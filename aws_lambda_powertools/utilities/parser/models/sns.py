from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel
from pydantic.networks import HttpUrl
from typing_extensions import Literal


class SqsMsgAttributeModel(BaseModel):
    Type: str
    Value: str


class SnsNotificationModel(BaseModel):
    Subject: Optional[str]
    TopicArn: str
    UnsubscribeUrl: HttpUrl
    Type: Literal["Notification"]
    MessageAttributes: Dict[str, SqsMsgAttributeModel]
    Message: str
    MessageId: str
    SigningCertUrl: HttpUrl
    Signature: str
    Timestamp: datetime
    SignatureVersion: str


class SnsRecordModel(BaseModel):
    EventSource: Literal["aws:sns"]
    EventVersion: str
    EventSubscriptionArn: str
    Sns: SnsNotificationModel


class SnsModel(BaseModel):
    Records: List[SnsRecordModel]
