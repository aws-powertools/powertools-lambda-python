from typing import Any, Dict, Iterator, List


class SESMailHeader:
    def __init__(self, header: Dict[str, str]):
        self._v = header

    @property
    def name(self) -> str:
        return self._v["name"]

    @property
    def value(self) -> str:
        return self._v["value"]


class SESMailCommonHeaders:
    def __init__(self, common_headers: Dict[str, Any]):
        self._v = common_headers

    @property
    def return_path(self) -> str:
        """The values in the Return-Path header of the email."""
        return self._v["returnPath"]

    @property
    def get_from(self) -> List[str]:
        """The values in the From header of the email."""
        # Note: this name conflicts with existing python builtins
        return self._v["from"]

    @property
    def date(self) -> List[str]:
        """The date and time when Amazon SES received the message."""
        return self._v["date"]

    @property
    def to(self) -> List[str]:
        """The values in the To header of the email."""
        return self._v["to"]

    @property
    def message_id(self) -> str:
        """The ID of the original message."""
        return str(self._v["messageId"])

    @property
    def subject(self) -> str:
        """The value of the Subject header for the email."""
        return str(self._v["subject"])


class SESMail:
    def __init__(self, mail: Dict[str, Any]):
        self._v = mail

    @property
    def timestamp(self) -> str:
        """String that contains the time at which the email was received, in ISO8601 format."""
        return self._v["timestamp"]

    @property
    def source(self) -> str:
        """String that contains the email address (specifically, the envelope MAIL FROM address)
        that the email was sent from."""
        return self._v["source"]

    @property
    def message_id(self) -> str:
        """String that contains the unique ID assigned to the email by Amazon SES.

        If the email was delivered to Amazon S3, the message ID is also the Amazon S3 object key that was
        used to write the message to your Amazon S3 bucket."""
        return self._v["messageId"]

    @property
    def destination(self) -> List[str]:
        """A complete list of all recipient addresses (including To: and CC: recipients)
        from the MIME headers of the incoming email."""
        return self._v["destination"]

    @property
    def headers_truncated(self) -> bool:
        """String that specifies whether the headers were truncated in the notification, which will happen
        if the headers are larger than 10 KB. Possible values are true and false."""
        return bool(self._v["headersTruncated"])

    @property
    def headers(self) -> Iterator[SESMailHeader]:
        """A list of Amazon SES headers and your custom headers.
        Each header in the list has a name field and a value field"""
        for header in self._v["headers"]:
            yield SESMailHeader(header)

    @property
    def common_headers(self) -> SESMailCommonHeaders:
        """A list of headers common to all emails. Each header in the list is composed of a name and a value."""
        return SESMailCommonHeaders(self._v["commonHeaders"])


class SESReceiptStatus:
    def __init__(self, receipt_status: Dict[str, str]):
        self._v = receipt_status

    @property
    def status(self) -> str:
        return str(self._v["status"])


class SESReceiptAction:
    def __init__(self, receipt_action: Dict[str, str]):
        self._v = receipt_action

    @property
    def get_type(self) -> str:
        """String that indicates the type of action that was executed.

        Possible values are S3, SNS, Bounce, Lambda, Stop, and WorkMail
        """
        # Note: this name conflicts with existing python builtins
        return self._v["type"]

    @property
    def function_arn(self) -> str:
        """String that contains the ARN of the Lambda function that was triggered.
        Present only for the Lambda action type."""
        return self._v["functionArn"]

    @property
    def invocation_type(self) -> str:
        """String that contains the invocation type of the Lambda function. Possible values are RequestResponse
        and Event. Present only for the Lambda action type."""
        return self._v["invocationType"]


class SESReceipt:
    def __init__(self, receipt: Dict[str, Any]):
        self._v = receipt

    @property
    def timestamp(self) -> str:
        """String that specifies the date and time at which the action was triggered, in ISO 8601 format."""
        return self._v["timestamp"]

    @property
    def processing_time_millis(self) -> int:
        """String that specifies the period, in milliseconds, from the time Amazon SES received the message
        to the time it triggered the action."""
        return int(self._v["processingTimeMillis"])

    @property
    def recipients(self) -> List[str]:
        """A list of recipients (specifically, the envelope RCPT TO addresses) that were matched by the
        active receipt rule. The addresses listed here may differ from those listed by the destination
        field in the mail object."""
        return self._v["recipients"]

    @property
    def spam_verdict(self) -> SESReceiptStatus:
        """Object that indicates whether the message is spam."""
        return SESReceiptStatus(self._v["spamVerdict"])

    @property
    def virus_verdict(self) -> SESReceiptStatus:
        """Object that indicates whether the message contains a virus."""
        return SESReceiptStatus(self._v["virusVerdict"])

    @property
    def spf_verdict(self) -> SESReceiptStatus:
        """Object that indicates whether the Sender Policy Framework (SPF) check passed."""
        return SESReceiptStatus(self._v["spfVerdict"])

    @property
    def dmarc_verdict(self) -> SESReceiptStatus:
        """Object that indicates whether the Domain-based Message Authentication,
        Reporting & Conformance (DMARC) check passed."""
        return SESReceiptStatus(self._v["dmarcVerdict"])

    @property
    def action(self) -> SESReceiptAction:
        """Object that encapsulates information about the action that was executed."""
        return SESReceiptAction(self._v["action"])


class SESMessage:
    def __init__(self, record: Dict[str, Any]):
        self._v = record

    @property
    def mail(self) -> SESMail:
        return SESMail(self._v["ses"]["mail"])

    @property
    def receipt(self) -> SESReceipt:
        return SESReceipt(self._v["ses"]["receipt"])


class SESEventRecord:
    def __init__(self, record: Dict[str, Any]):
        self._v = record

    @property
    def event_source(self) -> str:
        """The AWS service from which the SES event record originated. For SES, this is aws:ses"""
        return self._v["eventSource"]

    @property
    def event_version(self) -> str:
        return self._v["eventVersion"]

    @property
    def ses(self) -> SESMessage:
        return SESMessage(self._v)


class SESEvent(dict):
    """Amazon SES to receive message event trigger

    NOTE: There is a 30-second timeout on RequestResponse invocations.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/services-ses.html
    - https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email-action-lambda.html
    """

    @property
    def records(self) -> Iterator[SESEventRecord]:
        for record in self["Records"]:
            yield SESEventRecord(record)
