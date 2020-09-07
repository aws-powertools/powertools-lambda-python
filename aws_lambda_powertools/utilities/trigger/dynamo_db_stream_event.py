from enum import Enum
from typing import Dict, Iterator, List, Optional


class AttributeValue(dict):
    """Represents the data for an attribute

    Documentation: https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_streams_AttributeValue.html
    """

    @property
    def b_value(self) -> Optional[str]:
        """An attribute of type Base64-encoded binary data object"""
        return self.get("B")

    @property
    def bs_value(self) -> Optional[List[str]]:
        """An attribute of type Array of Base64-encoded binary data objects"""
        return self.get("BS")

    @property
    def bool_value(self) -> Optional[bool]:
        """An attribute of type Boolean"""
        item = self.get("bool")
        return None if item is None else bool(item)

    @property
    def list_value(self) -> Optional[List["AttributeValue"]]:
        """An attribute of type Array of AttributeValue objects"""
        item = self.get("L")
        return None if item is None else [AttributeValue(i) for i in item]

    @property
    def map_value(self) -> Optional[Dict[str, "AttributeValue"]]:
        """An attribute of type String to AttributeValue object map"""
        return _attribute_value(self, "M")

    @property
    def n_value(self) -> Optional[str]:
        """An attribute of type Number"""
        return self.get("N")

    @property
    def ns_value(self) -> Optional[List[str]]:
        """An attribute of type Number Set"""
        return self.get("NS")

    @property
    def null_value(self) -> Optional[bool]:
        """An attribute of type Null."""
        item = self.get("NULL")
        return None if item is None else bool(item)

    @property
    def s_value(self) -> Optional[str]:
        """An attribute of type String"""
        return self.get("S")

    @property
    def ss_value(self) -> Optional[List[str]]:
        """An attribute of type Array of strings"""
        return self.get("SS")


def _attribute_value(values: dict, key: str) -> Optional[Dict[str, AttributeValue]]:
    item: dict = values.get(key)
    return None if item is None else {k: AttributeValue(v) for k, v in item.items()}


class StreamViewType(Enum):
    """The type of data from the modified DynamoDB item that was captured in this stream record"""

    KEYS_ONLY = 0  # only the key attributes of the modified item
    NEW_IMAGE = 1  # the entire item, as it appeared after it was modified.
    OLD_IMAGE = 2  # the entire item, as it appeared before it was modified.
    NEW_AND_OLD_IMAGES = 3  # both the new and the old item images of the item.


class StreamRecord(dict):
    @property
    def approximate_creation_date_time(self) -> Optional[int]:
        """The approximate date and time when the stream record was created, in UNIX epoch time format."""
        item = self.get("ApproximateCreationDateTime")
        return None if item is None else int(item)

    @property
    def keys(self) -> Optional[Dict[str, AttributeValue]]:
        """The primary key attribute(s) for the DynamoDB item that was modified."""
        return _attribute_value(self, "Keys")

    @property
    def new_image(self) -> Optional[Dict[str, AttributeValue]]:
        """The item in the DynamoDB table as it appeared after it was modified."""
        return _attribute_value(self, "NewImage")

    @property
    def old_image(self) -> Optional[Dict[str, AttributeValue]]:
        """The item in the DynamoDB table as it appeared before it was modified."""
        return _attribute_value(self, "OldImage")

    @property
    def sequence_number(self) -> Optional[str]:
        """The sequence number of the stream record."""
        return self.get("SequenceNumber")

    @property
    def size_bytes(self) -> Optional[int]:
        """The size of the stream record, in bytes."""
        item = self.get("SizeBytes")
        return None if item is None else int(item)

    @property
    def stream_view_type(self) -> Optional[StreamViewType]:
        """The type of data from the modified DynamoDB item that was captured in this stream record"""
        item = self.get("StreamViewType")
        return None if item is None else StreamViewType[str(item)]


class DynamoDBRecordEventName(Enum):
    INSERT = 0  # a new item was added to the table
    MODIFY = 1  # one or more of an existing item's attributes were modified
    REMOVE = 2  # the item was deleted from the table


class DynamoDBRecord(dict):
    """A description of a unique event within a stream"""

    @property
    def aws_region(self) -> Optional[str]:
        """The region in which the GetRecords request was received"""
        return self.get("awsRegion")

    @property
    def dynamodb(self) -> Optional[StreamRecord]:
        """The main body of the stream record, containing all of the DynamoDB-specific fields."""
        item = self.get("dynamodb")
        return None if item is None else StreamRecord(item)

    @property
    def event_id(self) -> Optional[str]:
        """A globally unique identifier for the event that was recorded in this stream record."""
        return self.get("eventID")

    @property
    def event_name(self) -> Optional[DynamoDBRecordEventName]:
        """The type of data modification that was performed on the DynamoDB table"""
        item = self.get("eventName")
        return None if item is None else DynamoDBRecordEventName[item]

    @property
    def event_source(self) -> Optional[str]:
        """The AWS service from which the stream record originated. For DynamoDB Streams, this is aws:dynamodb."""
        return self.get("eventSource")

    @property
    def event_source_arn(self) -> Optional[str]:
        return self.get("eventSourceARN")

    @property
    def event_version(self) -> Optional[str]:
        """The version number of the stream record format."""
        return self.get("eventVersion")

    @property
    def user_identity(self) -> Optional[dict]:
        """Contains details about the type of identity that made the request"""
        return self.get("userIdentity")


class DynamoDBStreamEvent(dict):
    """Dynamo DB Stream Event

    Documentation: https://docs.aws.amazon.com/lambda/latest/dg/with-ddb.html
    """

    @property
    def records(self) -> Iterator[DynamoDBRecord]:
        for record in self["Records"]:
            yield DynamoDBRecord(record)
