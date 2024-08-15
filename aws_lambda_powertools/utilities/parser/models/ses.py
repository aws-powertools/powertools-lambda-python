from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import Literal

from pydantic import BaseModel, Field
from pydantic.types import PositiveInt  # noqa: TCH002


class SesReceiptVerdict(BaseModel):
    status: Literal["PASS", "FAIL", "GRAY", "PROCESSING_FAILED"]


class SesReceiptAction(BaseModel):
    type: Literal["Lambda"]  # noqa A003,VNE003
    invocationType: Literal["Event"]
    functionArn: str


class SesReceipt(BaseModel):
    timestamp: datetime
    processingTimeMillis: PositiveInt
    recipients: list[str]
    spamVerdict: SesReceiptVerdict
    virusVerdict: SesReceiptVerdict
    spfVerdict: SesReceiptVerdict
    dmarcVerdict: SesReceiptVerdict
    action: SesReceiptAction


class SesMailHeaders(BaseModel):
    name: str
    value: str


class SesMailCommonHeaders(BaseModel):
    header_from: list[str] = Field(None, alias="from")
    to: list[str]
    cc: list[str] | None = None
    bcc: list[str] | None = None
    sender: list[str] | None = None
    reply_to: list[str] | None = Field(None, alias="reply-to")
    returnPath: str
    messageId: str
    date: str
    subject: str


class SesMail(BaseModel):
    timestamp: datetime
    source: str
    messageId: str
    destination: list[str]
    headersTruncated: bool
    headers: list[SesMailHeaders]
    commonHeaders: SesMailCommonHeaders


class SesMessage(BaseModel):
    mail: SesMail
    receipt: SesReceipt


class SesRecordModel(BaseModel):
    eventSource: Literal["aws:ses"]
    eventVersion: str
    ses: SesMessage


class SesModel(BaseModel):
    Records: list[SesRecordModel]
