from typing import Dict, Iterator, Optional


class SQSRecordAttributes(dict):
    @property
    def aws_trace_header(self) -> Optional[str]:
        return self.get("AWSTraceHeader")

    @property
    def approximate_receive_count(self) -> str:
        return self["ApproximateReceiveCount"]

    @property
    def sent_timestamp(self) -> str:
        return self["SentTimestamp"]

    @property
    def sender_id(self) -> str:
        return self["SenderId"]

    @property
    def approximate_first_receive_timestamp(self) -> str:
        return self["ApproximateFirstReceiveTimestamp"]

    @property
    def sequence_number(self) -> Optional[str]:
        return self.get("SequenceNumber")

    @property
    def message_group_id(self) -> Optional[str]:
        return self.get("MessageGroupId")

    @property
    def message_deduplication_id(self) -> Optional[str]:
        return self.get("MessageDeduplicationId")


class SQSMessageAttribute(dict):
    @property
    def string_value(self) -> Optional[str]:
        return self["stringValue"]

    @property
    def binary_value(self) -> Optional[str]:
        return self["binaryValue"]

    @property
    def data_type(self) -> str:
        return self["dataType"]


class SQSMessageAttributes(Dict[str, SQSMessageAttribute]):
    def __getitem__(self, item) -> Optional[SQSMessageAttribute]:
        item = super(SQSMessageAttributes, self).get(item)
        return None if item is None else SQSMessageAttribute(item)


class SQSRecord(dict):
    @property
    def message_id(self) -> str:
        return self["messageId"]

    @property
    def receipt_handle(self) -> str:
        return self["receiptHandle"]

    @property
    def body(self) -> str:
        return self["body"]

    @property
    def attributes(self) -> SQSRecordAttributes:
        return SQSRecordAttributes(self["attributes"])

    @property
    def message_attributes(self) -> SQSMessageAttributes:
        return SQSMessageAttributes(self["messageAttributes"])

    @property
    def md5_of_body(self) -> str:
        return self["md5OfBody"]

    @property
    def event_source(self) -> str:
        return self["eventSource"]

    @property
    def event_source_arn(self) -> str:
        return self["eventSourceARN"]

    @property
    def aws_region(self) -> str:
        return self["awsRegion"]


class SQSEvent(dict):
    """SQS Event

    Documentation: https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
    """

    @property
    def records(self) -> Iterator[SQSRecord]:
        for record in self["Records"]:
            yield SQSRecord(record)
