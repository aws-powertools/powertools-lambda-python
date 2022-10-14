from datetime import datetime
from typing import Dict, List, Optional
from typing import Type as TypingType
from typing import Union

from pydantic import BaseModel, root_validator
from pydantic.networks import HttpUrl

from aws_lambda_powertools.utilities.parser.types import Literal


class SnsMsgAttributeModel(BaseModel):
    Type: str
    Value: str


class SnsNotificationModel(BaseModel):
    Subject: Optional[str]
    TopicArn: str
    UnsubscribeUrl: HttpUrl
    Type: Literal["Notification"]
    MessageAttributes: Optional[Dict[str, SnsMsgAttributeModel]]
    Message: Union[str, TypingType[BaseModel]]
    MessageId: str
    SigningCertUrl: Optional[HttpUrl]  # NOTE: FIFO opt-in removes attribute
    Signature: Optional[str]  # NOTE: FIFO opt-in removes attribute
    Timestamp: datetime
    SignatureVersion: Optional[str]  # NOTE: FIFO opt-in removes attribute

    @root_validator(pre=True, allow_reuse=True)
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
    Records: List[SnsRecordModel]
