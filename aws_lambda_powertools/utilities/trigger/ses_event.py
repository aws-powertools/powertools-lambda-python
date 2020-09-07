from typing import Iterator, List


class SESMailHeader(dict):
    @property
    def name(self) -> str:
        return self["name"]

    @property
    def value(self) -> str:
        return self["value"]


class SESMailCommonHeaders(dict):
    @property
    def return_path(self) -> str:
        return self["returnPath"]

    @property
    def from_header(self) -> List[str]:
        """Get the `from` common header as a list"""
        # Note: this conflicts with existing python builtins
        return self["from"]

    @property
    def date(self) -> List[str]:
        return self["date"]

    @property
    def to(self) -> List[str]:
        return self["to"]

    @property
    def message_id(self) -> str:
        return str(self["messageId"])

    @property
    def subject(self) -> str:
        return str(self["subject"])


class SESMail(dict):
    @property
    def timestamp(self) -> str:
        return self["timestamp"]

    @property
    def source(self) -> str:
        return self["source"]

    @property
    def message_id(self) -> str:
        return self["messageId"]

    @property
    def destination(self) -> List[str]:
        return self["destination"]

    @property
    def headers_truncated(self) -> bool:
        return bool(self["headersTruncated"])

    @property
    def headers(self) -> Iterator[SESMailHeader]:
        for header in self["headers"]:
            yield SESMailHeader(header)

    @property
    def common_headers(self) -> SESMailCommonHeaders:
        return SESMailCommonHeaders(self["commonHeaders"])


class SESReceiptStatus(dict):
    @property
    def status(self) -> str:
        return str(self["status"])


class SESReceiptAction(dict):
    @property
    def action_type(self) -> str:
        """Get the `type` property"""
        # Note: this conflicts with existing python builtins
        return self["type"]

    @property
    def function_arn(self) -> str:
        return self["functionArn"]

    @property
    def invocation_type(self) -> str:
        return self["invocationType"]


class SESReceipt(dict):
    @property
    def timestamp(self) -> str:
        return self["timestamp"]

    @property
    def processing_time_millis(self) -> int:
        return int(self["processingTimeMillis"])

    @property
    def recipients(self) -> List[str]:
        return self["recipients"]

    @property
    def spam_verdict(self) -> SESReceiptStatus:
        return SESReceiptStatus(self["spamVerdict"])

    @property
    def virus_verdict(self) -> SESReceiptStatus:
        return SESReceiptStatus(self["virusVerdict"])

    @property
    def spf_verdict(self) -> SESReceiptStatus:
        return SESReceiptStatus(self["spfVerdict"])

    @property
    def dmarc_verdict(self) -> SESReceiptStatus:
        return SESReceiptStatus(self["dmarcVerdict"])

    @property
    def action(self) -> SESReceiptAction:
        return SESReceiptAction(self["action"])


class SESMessage(dict):
    @property
    def mail(self) -> SESMail:
        return SESMail(self["mail"])

    @property
    def receipt(self) -> SESReceipt:
        return SESReceipt(self["receipt"])


class SESEventRecord(dict):
    @property
    def event_source(self) -> str:
        return self["eventSource"]

    @property
    def event_version(self) -> str:
        return self["eventVersion"]

    @property
    def ses(self) -> SESMessage:
        return SESMessage(self["ses"])


class SESEvent(dict):
    @property
    def records(self) -> Iterator[SESEventRecord]:
        for record in self["Records"]:
            yield SESEventRecord(record)
