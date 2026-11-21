from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, Field
from pydantic.types import PositiveInt


class SesReceiptVerdict(BaseModel):
    status: Literal["PASS", "FAIL", "GRAY", "PROCESSING_FAILED"]


class SesReceiptAction(BaseModel):
    type: Literal["Lambda"]  # noqa A003,VNE003
    invocationType: Literal["Event", "RequestResponse"] | None = None
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
    # SES sends each common header only when the email has that header
    header_from: list[str] | None = Field(None, alias="from")
    to: list[str] | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None
    sender: list[str] | None = None
    reply_to: list[str] | None = Field(
        None,
        validation_alias=AliasChoices("replyTo", "reply-to", "reply_to"),
        serialization_alias="replyTo",
    )
    returnPath: str | None = None
    messageId: str | None = None
    date: str | None = None
    subject: str | None = None


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
