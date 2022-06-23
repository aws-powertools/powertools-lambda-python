import logging
import sys
from datetime import datetime
from typing import List, NewType, Optional

from pydantic import BaseModel, Field
from pydantic.types import PositiveInt

from ..types import Literal

has_email_validator = "email_validator" in sys.modules

if has_email_validator:
    from pydantic.networks import EmailStr
else:
    logging.warning("email_validator package is not installed")
    EmailStr = NewType("EmailStr", str)  # type: ignore[no-redef, misc]


class SesReceiptVerdict(BaseModel):
    status: Literal["PASS", "FAIL", "GRAY", "PROCESSING_FAILED"]


class SesReceiptAction(BaseModel):
    type: Literal["Lambda"]  # noqa A003,VNE003
    invocationType: Literal["Event"]
    functionArn: str


class SesReceipt(BaseModel):
    timestamp: datetime
    processingTimeMillis: PositiveInt
    recipients: List[EmailStr]
    spamVerdict: SesReceiptVerdict
    virusVerdict: SesReceiptVerdict
    spfVerdict: SesReceiptVerdict
    dmarcVerdict: SesReceiptVerdict
    action: SesReceiptAction


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
