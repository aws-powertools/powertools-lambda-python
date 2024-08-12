from __future__ import annotations

from enum import Enum
from functools import cached_property
from typing import Any, Iterator

from aws_lambda_powertools.shared.dynamodb_deserializer import TypeDeserializer
from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class StreamViewType(Enum):
    """The type of data from the modified DynamoDB item that was captured in this stream record"""

    KEYS_ONLY = 0  # only the key attributes of the modified item
    NEW_IMAGE = 1  # the entire item, as it appeared after it was modified.
    OLD_IMAGE = 2  # the entire item, as it appeared before it was modified.
    NEW_AND_OLD_IMAGES = 3  # both the new and the old item images of the item.


class StreamRecord(DictWrapper):
    _deserializer = TypeDeserializer()

    def __init__(self, data: dict[str, Any]):
        """StreamRecord constructor
        Parameters
        ----------
        data: dict[str, Any]
            Represents the dynamodb dict inside DynamoDBStreamEvent's records
        """
        super().__init__(data)
        self._deserializer = TypeDeserializer()

    def _deserialize_dynamodb_dict(self, key: str) -> dict[str, Any]:
        """Deserialize DynamoDB records available in `Keys`, `NewImage`, and `OldImage`

        Parameters
        ----------
        key : str
            DynamoDB key (e.g., Keys, NewImage, or OldImage)

        Returns
        -------
        dict[str, Any]
            Deserialized records in Python native types
        """
        dynamodb_dict = self._data.get(key) or {}
        return {k: self._deserializer.deserialize(v) for k, v in dynamodb_dict.items()}

    @property
    def approximate_creation_date_time(self) -> int | None:
        """The approximate date and time when the stream record was created, in UNIX epoch time format."""
        item = self.get("ApproximateCreationDateTime")
        return None if item is None else int(item)

    @cached_property
    def keys(self) -> dict[str, Any]:  # type: ignore[override]
        """The primary key attribute(s) for the DynamoDB item that was modified."""
        return self._deserialize_dynamodb_dict("Keys")

    @cached_property
    def new_image(self) -> dict[str, Any]:
        """The item in the DynamoDB table as it appeared after it was modified."""
        return self._deserialize_dynamodb_dict("NewImage")

    @cached_property
    def old_image(self) -> dict[str, Any]:
        """The item in the DynamoDB table as it appeared before it was modified."""
        return self._deserialize_dynamodb_dict("OldImage")

    @property
    def sequence_number(self) -> str | None:
        """The sequence number of the stream record."""
        return self.get("SequenceNumber")

    @property
    def size_bytes(self) -> int | None:
        """The size of the stream record, in bytes."""
        item = self.get("SizeBytes")
        return None if item is None else int(item)

    @property
    def stream_view_type(self) -> StreamViewType | None:
        """The type of data from the modified DynamoDB item that was captured in this stream record"""
        item = self.get("StreamViewType")
        return None if item is None else StreamViewType[str(item)]


class DynamoDBRecordEventName(Enum):
    INSERT = 0  # a new item was added to the table
    MODIFY = 1  # one or more of an existing item's attributes were modified
    REMOVE = 2  # the item was deleted from the table


class DynamoDBRecord(DictWrapper):
    """A description of a unique event within a stream"""

    @property
    def aws_region(self) -> str | None:
        """The region in which the GetRecords request was received"""
        return self.get("awsRegion")

    @property
    def dynamodb(self) -> StreamRecord | None:
        """The main body of the stream record, containing all the DynamoDB-specific dicts."""
        stream_record = self.get("dynamodb")
        return None if stream_record is None else StreamRecord(stream_record)

    @property
    def event_id(self) -> str | None:
        """A globally unique identifier for the event that was recorded in this stream record."""
        return self.get("eventID")

    @property
    def event_name(self) -> DynamoDBRecordEventName | None:
        """The type of data modification that was performed on the DynamoDB table"""
        item = self.get("eventName")
        return None if item is None else DynamoDBRecordEventName[item]

    @property
    def event_source(self) -> str | None:
        """The AWS service from which the stream record originated. For DynamoDB Streams, this is aws:dynamodb."""
        return self.get("eventSource")

    @property
    def event_source_arn(self) -> str | None:
        """The Amazon Resource Name (ARN) of the event source"""
        return self.get("eventSourceARN")

    @property
    def event_version(self) -> str | None:
        """The version number of the stream record format."""
        return self.get("eventVersion")

    @property
    def user_identity(self) -> dict:
        """Contains details about the type of identity that made the request"""
        return self.get("userIdentity") or {}


class DynamoDBStreamEvent(DictWrapper):
    """Dynamo DB Stream Event

    Documentation:
    -------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-ddb.html

    Example
    -------
    **Process dynamodb stream events. DynamoDB types are automatically converted to their equivalent Python values.**

        from aws_lambda_powertools.utilities.data_classes import event_source, DynamoDBStreamEvent
        from aws_lambda_powertools.utilities.typing import LambdaContext


        @event_source(data_class=DynamoDBStreamEvent)
        def lambda_handler(event: DynamoDBStreamEvent, context: LambdaContext):
            for record in event.records:
                # {"N": "123.45"} => Decimal("123.45")
                key: str = record.dynamodb.keys["id"]
                print(key)
    """

    @property
    def records(self) -> Iterator[DynamoDBRecord]:
        for record in self["Records"]:
            yield DynamoDBRecord(record)
