from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, ItemsView, Iterator, TypeVar

from aws_lambda_powertools.utilities.data_classes import S3Event
from aws_lambda_powertools.utilities.data_classes.common import DictWrapper
from aws_lambda_powertools.utilities.data_classes.sns_event import SNSMessage

if TYPE_CHECKING:
    from collections.abc import Iterator


class SQSRecordAttributes(DictWrapper):
    @property
    def aws_trace_header(self) -> str | None:
        """Returns the AWS X-Ray trace header string."""
        return self.get("AWSTraceHeader")

    @property
    def approximate_receive_count(self) -> str:
        """Returns the number of times a message has been received across all queues but not deleted."""
        return self["ApproximateReceiveCount"]

    @property
    def sent_timestamp(self) -> str:
        """Returns the time the message was sent to the queue (epoch time in milliseconds)."""
        return self["SentTimestamp"]

    @property
    def sender_id(self) -> str:
        """For an IAM user, returns the IAM user ID, For an IAM role, returns the IAM role ID"""
        return self["SenderId"]

    @property
    def approximate_first_receive_timestamp(self) -> str:
        """Returns the time the message was first received from the queue (epoch time in milliseconds)."""
        return self["ApproximateFirstReceiveTimestamp"]

    @property
    def sequence_number(self) -> str | None:
        """The large, non-consecutive number that Amazon SQS assigns to each message."""
        return self.get("SequenceNumber")

    @property
    def message_group_id(self) -> str | None:
        """The tag that specifies that a message belongs to a specific message group.

        Messages that belong to the same message group are always processed one by one, in a
        strict order relative to the message group (however, messages that belong to different
        message groups might be processed out of order)."""
        return self.get("MessageGroupId")

    @property
    def message_deduplication_id(self) -> str | None:
        """The token used for deduplication of sent messages.

        If a message with a particular message deduplication ID is sent successfully, any messages sent
        with the same message deduplication ID are accepted successfully but aren't delivered during
        the 5-minute deduplication interval."""
        return self.get("MessageDeduplicationId")

    @property
    def dead_letter_queue_source_arn(self) -> str | None:
        """The SQS queue ARN that sent the record to this DLQ.
        Only present when a Lambda function is using a DLQ as an event source.
        """
        return self.get("DeadLetterQueueSourceArn")


class SQSMessageAttribute(DictWrapper):
    """The user-specified message attribute value."""

    @property
    def string_value(self) -> str | None:
        """Strings are Unicode with UTF-8 binary encoding."""
        return self["stringValue"]

    @property
    def binary_value(self) -> str | None:
        """Binary type attributes can store any binary data, such as compressed data, encrypted data, or images.

        Base64-encoded binary data object"""
        return self["binaryValue"]

    @property
    def data_type(self) -> str:
        """The message attribute data type. Supported types include `String`, `Number`, and `Binary`."""
        return self["dataType"]


class SQSMessageAttributes(dict[str, SQSMessageAttribute]):
    def __getitem__(self, key: str) -> SQSMessageAttribute | None:  # type: ignore
        item = super().get(key)
        return None if item is None else SQSMessageAttribute(item)  # type: ignore

    def items(self) -> ItemsView[str, SQSMessageAttribute]:  # type: ignore
        return {k: SQSMessageAttribute(v) for k, v in super().items()}.items()  # type: ignore


class SQSRecord(DictWrapper):
    """An Amazon SQS message"""

    NestedEvent = TypeVar("NestedEvent", bound=DictWrapper)

    @property
    def message_id(self) -> str:
        """A unique identifier for the message.

        A messageId is considered unique across all AWS accounts for an extended period of time."""
        return self["messageId"]

    @property
    def receipt_handle(self) -> str:
        """An identifier associated with the act of receiving the message.

        A new receipt handle is returned every time you receive a message. When deleting a message,
        you provide the last received receipt handle to delete the message."""
        return self["receiptHandle"]

    @property
    def body(self) -> str:
        """The message's contents (not URL-encoded)."""
        return self["body"]

    @cached_property
    def json_body(self) -> Any:
        """Deserializes JSON string available in 'body' property

        Notes
        -----

        **Strict typing**

        Caller controls the type as we can't use recursive generics here.

        JSON Union types would force caller to have to cast a type. Instead,
        we choose Any to ease ergonomics and other tools receiving this data.

        Examples
        --------

        **Type deserialized data from JSON string**

        ```python
        data: dict = record.json_body  # {"telemetry": [], ...}
        # or
        data: list = record.json_body  # ["telemetry_values"]
        ```
        """
        return self._json_deserializer(self["body"])

    @property
    def attributes(self) -> SQSRecordAttributes:
        """A map of the attributes requested in ReceiveMessage to their respective values."""
        return SQSRecordAttributes(self["attributes"])

    @property
    def message_attributes(self) -> SQSMessageAttributes:
        """Each message attribute consists of a Name, Type, and Value."""
        return SQSMessageAttributes(self["messageAttributes"])

    @property
    def md5_of_body(self) -> str:
        """An MD5 digest of the non-URL-encoded message body string."""
        return self["md5OfBody"]

    @property
    def event_source(self) -> str:
        """The AWS service from which the SQS record originated. For SQS, this is `aws:sqs`"""
        return self["eventSource"]

    @property
    def event_source_arn(self) -> str:
        """The Amazon Resource Name (ARN) of the event source"""
        return self["eventSourceARN"]

    @property
    def aws_region(self) -> str:
        """aws region eg: us-east-1"""
        return self["awsRegion"]

    @property
    def queue_url(self) -> str:
        """The URL of the queue."""
        arn_parts = self["eventSourceARN"].split(":")
        region = arn_parts[3]
        account_id = arn_parts[4]
        queue_name = arn_parts[5]

        queue_url = f"https://sqs.{region}.amazonaws.com/{account_id}/{queue_name}"

        return queue_url

    @property
    def decoded_nested_s3_event(self) -> S3Event:
        """Returns the nested `S3Event` object that is sent in the body of a SQS message.

        Even though you can typecast the object returned by `record.json_body`
        directly, this method is provided as a shortcut for convenience.

        Notes
        -----

        This method does not validate whether the SQS message body is actually a valid S3 event.

        Examples
        --------

        ```python
        nested_event: S3Event = record.decoded_nested_s3_event
        ```
        """
        return self._decode_nested_event(S3Event)

    @property
    def decoded_nested_sns_event(self) -> SNSMessage:
        """Returns the nested `SNSMessage` object that is sent in the body of a SQS message.

        Even though you can typecast the object returned by `record.json_body`
        directly, this method is provided as a shortcut for convenience.

        Notes
        -----

        This method does not validate whether the SQS message body is actually
        a valid SNS message.

        Examples
        --------

        ```python
        nested_message: SNSMessage = record.decoded_nested_sns_event
        ```
        """
        return self._decode_nested_event(SNSMessage)

    def _decode_nested_event(self, nested_event_class: type[NestedEvent]) -> NestedEvent:
        """Returns the nested event source data object.

        This is useful for handling events that are sent in the body of a SQS message.

        Examples
        --------

        ```python
        data: S3Event = self._decode_nested_event(S3Event)
        ```
        """
        return nested_event_class(self.json_body)


class SQSEvent(DictWrapper):
    """SQS Event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
    """

    @property
    def records(self) -> Iterator[SQSRecord]:
        for record in self["Records"]:
            yield SQSRecord(data=record, json_deserializer=self._json_deserializer)
