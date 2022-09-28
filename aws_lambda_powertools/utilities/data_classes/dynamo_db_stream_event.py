from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Union

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class AttributeValueType(Enum):
    Binary = "B"
    BinarySet = "BS"
    Boolean = "BOOL"
    List = "L"
    Map = "M"
    Number = "N"
    NumberSet = "NS"
    Null = "NULL"
    String = "S"
    StringSet = "SS"


class AttributeValue(DictWrapper):
    """Represents the data for an attribute

    Documentation:
    --------------
    - https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_streams_AttributeValue.html
    - https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.NamingRulesDataTypes.html
    """

    def __init__(self, data: Dict[str, Any]):
        """AttributeValue constructor

        Parameters
        ----------
        data: Dict[str, Any]
            Raw lambda event dict
        """
        super().__init__(data)
        self.dynamodb_type = list(data.keys())[0]

    @property
    def b_value(self) -> Optional[str]:
        """An attribute of type Base64-encoded binary data object

        Example:
            >>> {"B": "dGhpcyB0ZXh0IGlzIGJhc2U2NC1lbmNvZGVk"}
        """
        return self.get("B")

    @property
    def bs_value(self) -> Optional[List[str]]:
        """An attribute of type Array of Base64-encoded binary data objects

        Example:
            >>> {"BS": ["U3Vubnk=", "UmFpbnk=", "U25vd3k="]}
        """
        return self.get("BS")

    @property
    def bool_value(self) -> Optional[bool]:
        """An attribute of type Boolean

        Example:
            >>> {"BOOL": True}
        """
        item = self.get("BOOL")
        return None if item is None else bool(item)

    @property
    def list_value(self) -> Optional[List["AttributeValue"]]:
        """An attribute of type Array of AttributeValue objects

        Example:
            >>> {"L": [ {"S": "Cookies"} , {"S": "Coffee"}, {"N": "3.14159"}]}
        """
        item = self.get("L")
        return None if item is None else [AttributeValue(v) for v in item]

    @property
    def map_value(self) -> Optional[Dict[str, "AttributeValue"]]:
        """An attribute of type String to AttributeValue object map

        Example:
            >>> {"M": {"Name": {"S": "Joe"}, "Age": {"N": "35"}}}
        """
        return _attribute_value_dict(self._data, "M")

    @property
    def n_value(self) -> Optional[str]:
        """An attribute of type Number

        Numbers are sent across the network to DynamoDB as strings, to maximize compatibility across languages
        and libraries. However, DynamoDB treats them as number type attributes for mathematical operations.

        Example:
            >>> {"N": "123.45"}
        """
        return self.get("N")

    @property
    def ns_value(self) -> Optional[List[str]]:
        """An attribute of type Number Set

        Example:
            >>> {"NS": ["42.2", "-19", "7.5", "3.14"]}
        """
        return self.get("NS")

    @property
    def null_value(self) -> None:
        """An attribute of type Null.

        Example:
            >>> {"NULL": True}
        """
        return None

    @property
    def s_value(self) -> Optional[str]:
        """An attribute of type String

        Example:
            >>> {"S": "Hello"}
        """
        return self.get("S")

    @property
    def ss_value(self) -> Optional[List[str]]:
        """An attribute of type Array of strings

        Example:
            >>> {"SS": ["Giraffe", "Hippo" ,"Zebra"]}
        """
        return self.get("SS")

    @property
    def get_type(self) -> AttributeValueType:
        """Get the attribute value type based on the contained data"""
        return AttributeValueType(self.dynamodb_type)

    @property
    def l_value(self) -> Optional[List["AttributeValue"]]:
        """Alias of list_value"""
        return self.list_value

    @property
    def m_value(self) -> Optional[Dict[str, "AttributeValue"]]:
        """Alias of map_value"""
        return self.map_value

    @property
    def get_value(self) -> Union[Optional[bool], Optional[str], Optional[List], Optional[Dict]]:
        """Get the attribute value"""
        try:
            return getattr(self, f"{self.dynamodb_type.lower()}_value")
        except AttributeError:
            raise TypeError(f"Dynamodb type {self.dynamodb_type} is not supported")


def _attribute_value_dict(attr_values: Dict[str, dict], key: str) -> Optional[Dict[str, AttributeValue]]:
    """A dict of type String to AttributeValue object map

    Example:
        >>> {"NewImage": {"Id": {"S": "xxx-xxx"}, "Value": {"N": "35"}}}
    """
    attr_values_dict = attr_values.get(key)
    return None if attr_values_dict is None else {k: AttributeValue(v) for k, v in attr_values_dict.items()}


class StreamViewType(Enum):
    """The type of data from the modified DynamoDB item that was captured in this stream record"""

    KEYS_ONLY = 0  # only the key attributes of the modified item
    NEW_IMAGE = 1  # the entire item, as it appeared after it was modified.
    OLD_IMAGE = 2  # the entire item, as it appeared before it was modified.
    NEW_AND_OLD_IMAGES = 3  # both the new and the old item images of the item.


class StreamRecord(DictWrapper):
    @property
    def approximate_creation_date_time(self) -> Optional[int]:
        """The approximate date and time when the stream record was created, in UNIX epoch time format."""
        item = self.get("ApproximateCreationDateTime")
        return None if item is None else int(item)

    # NOTE: This override breaks the Mapping protocol of DictWrapper, it's left here for backwards compatibility with
    # a 'type: ignore' comment. See #1516 for discussion
    @property
    def keys(self) -> Optional[Dict[str, AttributeValue]]:  # type: ignore[override]
        """The primary key attribute(s) for the DynamoDB item that was modified."""
        return _attribute_value_dict(self._data, "Keys")

    @property
    def new_image(self) -> Optional[Dict[str, AttributeValue]]:
        """The item in the DynamoDB table as it appeared after it was modified."""
        return _attribute_value_dict(self._data, "NewImage")

    @property
    def old_image(self) -> Optional[Dict[str, AttributeValue]]:
        """The item in the DynamoDB table as it appeared before it was modified."""
        return _attribute_value_dict(self._data, "OldImage")

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


class DynamoDBRecord(DictWrapper):
    """A description of a unique event within a stream"""

    @property
    def aws_region(self) -> Optional[str]:
        """The region in which the GetRecords request was received"""
        return self.get("awsRegion")

    @property
    def dynamodb(self) -> Optional[StreamRecord]:
        """The main body of the stream record, containing all the DynamoDB-specific fields."""
        stream_record = self.get("dynamodb")
        return None if stream_record is None else StreamRecord(stream_record)

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
        """The Amazon Resource Name (ARN) of the event source"""
        return self.get("eventSourceARN")

    @property
    def event_version(self) -> Optional[str]:
        """The version number of the stream record format."""
        return self.get("eventVersion")

    @property
    def user_identity(self) -> Optional[dict]:
        """Contains details about the type of identity that made the request"""
        return self.get("userIdentity")


class DynamoDBStreamEvent(DictWrapper):
    """Dynamo DB Stream Event

    Documentation:
    -------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-ddb.html

    Example
    -------
    **Process dynamodb stream events and use get_type and get_value for handling conversions**

        from aws_lambda_powertools.utilities.data_classes import event_source, DynamoDBStreamEvent
        from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
            AttributeValueType,
            AttributeValue,
        )
        from aws_lambda_powertools.utilities.typing import LambdaContext


        @event_source(data_class=DynamoDBStreamEvent)
        def lambda_handler(event: DynamoDBStreamEvent, context: LambdaContext):
            for record in event.records:
                key: AttributeValue = record.dynamodb.keys["id"]
                if key == AttributeValueType.Number:
                    assert key.get_value == key.n_value
                    print(key.get_value)
                elif key == AttributeValueType.Map:
                    assert key.get_value == key.map_value
                    print(key.get_value)
    """

    @property
    def records(self) -> Iterator[DynamoDBRecord]:
        for record in self["Records"]:
            yield DynamoDBRecord(record)
