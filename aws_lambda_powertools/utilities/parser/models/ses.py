from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field
from pydantic.networks import EmailStr
from pydantic.types import PositiveInt

from ..types import Literal


class SesReceiptVerdict(BaseModel):
    status: Literal["PASS", "FAIL", "GRAY", "PROCESSING_FAILED"]


class SesReceiptActionBase(BaseModel):
    topicArn: Optional[str]


class SesReceiptAction(SesReceiptActionBase):
    type: Literal["Lambda"]  # noqa A003,VNE003
    invocationType: Literal["Event"]
    functionArn: str


class SesReceiptS3Action(SesReceiptActionBase):
    type: Literal["S3"]  # noqa A003,VNE003
    topicArn: str
    bucketName: str
    objectKey: str


class SesReceiptBounceAction(SesReceiptActionBase):
    type: Literal["Bounce"]  # noqa A003,VNE003
    topicArn: str
    smtpReplyCode: str
    message: str
    sender: str
    statusCode: str


class SesReceiptWorkmailAction(SesReceiptActionBase):
    type: Literal["WorkMail"]  # noqa A003,VNE003
    topicArn: str
    organizationArn: str


class SesReceipt(BaseModel):
    timestamp: datetime
    processingTimeMillis: PositiveInt
    recipients: List[EmailStr]
    spamVerdict: SesReceiptVerdict
    virusVerdict: SesReceiptVerdict
    spfVerdict: SesReceiptVerdict
    dkimVerdict: SesReceiptVerdict
    dmarcVerdict: SesReceiptVerdict
    dmarcPolicy: Optional[Literal["quarantine", "reject", "none"]]
    action: Union[SesReceiptAction, SesReceiptS3Action, SesReceiptBounceAction, SesReceiptWorkmailAction]


class SesMailHeaders(BaseModel):
    name: str
    value: str


class SesMailCommonHeaders(BaseModel):
    header_from: List[str] = Field(None, alias="from")
    to: List[str]
    cc: Optional[List[str]]
    bcc: Optional[List[str]]
    sender: Optional[List[str]]
    reply_to: Optional[List[str]] = Field(None, alias="reply-to")
    returnPath: EmailStr
    messageId: str
    date: str
    subject: str


class SesMail(BaseModel):
    timestamp: datetime
    source: EmailStr
    messageId: str
    destination: List[EmailStr]
    headersTruncated: bool
    headers: List[SesMailHeaders]
    commonHeaders: SesMailCommonHeaders


class SesMessage(BaseModel):
    mail: SesMail
    receipt: SesReceipt


class SesRecordModel(BaseModel):
    eventSource: Literal["aws:ses"]
    eventVersion: str
    ses: SesMessage


class SesModel(BaseModel):
    Records: List[SesRecordModel]
