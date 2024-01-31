from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic.types import PositiveInt

from ..types import Literal


class SesReceiptVerdict(BaseModel):
    status: Literal["PASS", "FAIL", "GRAY", "PROCESSING_FAILED"]


class SesReceiptAction(BaseModel):
    type: Literal["Lambda"]  # noqa A003,VNE003
    invocationType: Literal["Event"]
    functionArn: str


class SesReceipt(BaseModel):
    timestamp: datetime
    processingTimeMillis: PositiveInt
    recipients: List[str]
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
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    sender: Optional[List[str]] = None
    reply_to: Optional[List[str]] = Field(None, alias="reply-to")
    returnPath: str
    messageId: str
    date: str
    subject: str


class SesMail(BaseModel):
    timestamp: datetime
    source: str
    messageId: str
    destination: List[str]
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
