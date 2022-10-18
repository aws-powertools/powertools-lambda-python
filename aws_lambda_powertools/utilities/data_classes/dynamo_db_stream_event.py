from enum import Enum
from typing import Any, Dict, Iterator, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class TypeDeserializer:
    """
    This class deserializes DynamoDB types to Python types.
    It based on boto3's DynamoDB TypeDeserializer found here:
    https://boto3.amazonaws.com/v1/documentation/api/latest/_modules/boto3/dynamodb/types.html
    Except that it deserializes DynamoDB numbers into strings, and does not wrap binary
    with a Binary class.
    """

    def deserialize(self, value):
        """The method to deserialize the DynamoDB data types.

        :param value: A DynamoDB value to be deserialized to a pythonic value.
            Here are the various conversions:

            DynamoDB                                Python
            --------                                ------
            {'NULL': True}                          None
            {'BOOL': True/False}                    True/False
            {'N': str(value)}                       str(value)
            {'S': string}                           string
            {'B': bytes}                            bytes
            {'NS': [str(value)]}                    set([str(value)])
            {'SS': [string]}                        set([string])
            {'BS': [bytes]}                         set([bytes])
            {'L': list}                             list
            {'M': dict}                             dict

        :returns: The pythonic value of the DynamoDB type.
        """

        if not value:
            raise TypeError("Value must be a nonempty dictionary whose key " "is a valid dynamodb type.")
        dynamodb_type = list(value.keys())[0]
        try:
            deserializer = getattr(self, f"_deserialize_{dynamodb_type}".lower())
        except AttributeError:
            raise TypeError(f"Dynamodb type {dynamodb_type} is not supported")
        return deserializer(value[dynamodb_type])

    def _deserialize_null(self, value):
        return None

    def _deserialize_bool(self, value):
        return value

    def _deserialize_n(self, value):
        return value

    def _deserialize_s(self, value):
        return value

    def _deserialize_b(self, value):
        return value

    def _deserialize_ns(self, value):
        return set(map(self._deserialize_n, value))

    def _deserialize_ss(self, value):
        return set(map(self._deserialize_s, value))

    def _deserialize_bs(self, value):
        return set(map(self._deserialize_b, value))

    def _deserialize_l(self, value):
        return [self.deserialize(v) for v in value]

    def _deserialize_m(self, value):
        return {k: self.deserialize(v) for k, v in value.items()}


class StreamViewType(Enum):
    """The type of data from the modified DynamoDB item that was captured in this stream record"""

    KEYS_ONLY = 0  # only the key attributes of the modified item
    NEW_IMAGE = 1  # the entire item, as it appeared after it was modified.
    OLD_IMAGE = 2  # the entire item, as it appeared before it was modified.
    NEW_AND_OLD_IMAGES = 3  # both the new and the old item images of the item.


class StreamRecord(DictWrapper):
    def __init__(self, data: Dict[str, Any]):
        """StreamRecord constructor

        Parameters
        ----------
        data: Dict[str, Any]
            Represents the dynamodb dict inside DynamoDBStreamEvent's records
        """
        super().__init__(data)
        self._deserializer = TypeDeserializer()

    def _deserialize_dynamodb_dict(self, key: str) -> Optional[Dict[str, Any]]:
        dynamodb_dict = self._data.get(key)
        return (
            None if dynamodb_dict is None else {k: self._deserializer.deserialize(v) for k, v in dynamodb_dict.items()}
        )

    @property
    def approximate_creation_date_time(self) -> Optional[int]:
        """The approximate date and time when the stream record was created, in UNIX epoch time format."""
        item = self.get("ApproximateCreationDateTime")
        return None if item is None else int(item)

    @property
    def keys(self) -> Optional[Dict[str, Any]]:  # type: ignore[override]
        """The primary key attribute(s) for the DynamoDB item that was modified."""
        return self._deserialize_dynamodb_dict("Keys")

    @property
    def new_image(self) -> Optional[Dict[str, Any]]:
        """The item in the DynamoDB table as it appeared after it was modified."""
        return self._deserialize_dynamodb_dict("NewImage")

    @property
    def old_image(self) -> Optional[Dict[str, Any]]:
        """The item in the DynamoDB table as it appeared before it was modified."""
        return self._deserialize_dynamodb_dict("OldImage")

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
        """The main body of the stream record, containing all the DynamoDB-specific dicts."""
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
