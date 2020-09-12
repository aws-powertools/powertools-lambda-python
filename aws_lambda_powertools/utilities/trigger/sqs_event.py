from typing import Any, Dict, Iterator, Optional


class SQSRecordAttributes:
    def __init__(self, record_attributes: Dict[str, str]):
        self._v = record_attributes

    @property
    def aws_trace_header(self) -> Optional[str]:
        """Returns the AWS X-Ray trace header string."""
        return self._v.get("AWSTraceHeader")

    @property
    def approximate_receive_count(self) -> str:
        """Returns the number of times a message has been received across all queues but not deleted."""
        return self._v["ApproximateReceiveCount"]

    @property
    def sent_timestamp(self) -> str:
        """Returns the time the message was sent to the queue (epoch time in milliseconds)."""
        return self._v["SentTimestamp"]

    @property
    def sender_id(self) -> str:
        """For an IAM user, returns the IAM user ID, For an IAM role, returns the IAM role ID"""
        return self._v["SenderId"]

    @property
    def approximate_first_receive_timestamp(self) -> str:
        """Returns the time the message was first received from the queue (epoch time in milliseconds)."""
        return self._v["ApproximateFirstReceiveTimestamp"]

    @property
    def sequence_number(self) -> Optional[str]:
        """The large, non-consecutive number that Amazon SQS assigns to each message."""
        return self._v.get("SequenceNumber")

    @property
    def message_group_id(self) -> Optional[str]:
        """The tag that specifies that a message belongs to a specific message group.

        Messages that belong to the same message group are always processed one by one, in a
        strict order relative to the message group (however, messages that belong to different
        message groups might be processed out of order)."""
        return self._v.get("MessageGroupId")

    @property
    def message_deduplication_id(self) -> Optional[str]:
        """The token used for deduplication of sent messages.

        If a message with a particular message deduplication ID is sent successfully, any messages sent
        with the same message deduplication ID are accepted successfully but aren't delivered during
        the 5-minute deduplication interval."""
        return self._v.get("MessageDeduplicationId")


class SQSMessageAttribute:
    """The user-specified message attribute value."""

    def __init__(self, message_attribute: Dict[str, str]):
        self._v = message_attribute

    @property
    def string_value(self) -> Optional[str]:
        """Strings are Unicode with UTF-8 binary encoding."""
        return self._v["stringValue"]

    @property
    def binary_value(self) -> Optional[str]:
        """Binary type attributes can store any binary data, such as compressed data, encrypted data, or images.

        Base64-encoded binary data object"""
        return self._v["binaryValue"]

    @property
    def data_type(self) -> str:
        """ The message attribute data type. Supported types include `String`, `Number`, and `Binary`."""
        return self._v["dataType"]


class SQSMessageAttributes(Dict[str, SQSMessageAttribute]):
    def __getitem__(self, key: str) -> Optional[SQSMessageAttribute]:
        item = super(SQSMessageAttributes, self).get(key)
        return None if item is None else SQSMessageAttribute(item)


class SQSRecord:
    """An Amazon SQS message"""

    def __init__(self, record: Dict[str, Any]):
        self._v = record

    @property
    def message_id(self) -> str:
        """A unique identifier for the message.

        A messageId is considered unique across all AWS accounts for an extended period of time."""
        return self._v["messageId"]

    @property
    def receipt_handle(self) -> str:
        """An identifier associated with the act of receiving the message.

        A new receipt handle is returned every time you receive a message. When deleting a message,
        you provide the last received receipt handle to delete the message."""
        return self._v["receiptHandle"]

    @property
    def body(self) -> str:
        """The message's contents (not URL-encoded)."""
        return self._v["body"]

    @property
    def attributes(self) -> SQSRecordAttributes:
        """A map of the attributes requested in ReceiveMessage to their respective values."""
        return SQSRecordAttributes(self._v["attributes"])

    @property
    def message_attributes(self) -> SQSMessageAttributes:
        """Each message attribute consists of a Name, Type, and Value."""
        return SQSMessageAttributes(self._v["messageAttributes"])

    @property
    def md5_of_body(self) -> str:
        """An MD5 digest of the non-URL-encoded message body string."""
        return self._v["md5OfBody"]

    @property
    def event_source(self) -> str:
        """The AWS service from which the SQS record originated. For SQS, this is `aws:sqs` """
        return self._v["eventSource"]

    @property
    def event_source_arn(self) -> str:
        """The Amazon Resource Name (ARN) of the event source"""
        return self._v["eventSourceARN"]

    @property
    def aws_region(self) -> str:
        """aws region eg: us-east-1"""
        return self._v["awsRegion"]


class SQSEvent(dict):
    """SQS Event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
    """

    @property
    def records(self) -> Iterator[SQSRecord]:
        for record in self["Records"]:
            yield SQSRecord(record)
