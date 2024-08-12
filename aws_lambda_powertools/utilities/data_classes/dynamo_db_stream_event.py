from decimal import Clamped, Context, Decimal, Inexact, Overflow, Rounded, Underflow
from enum import Enum
from typing import Any, Callable, Dict, Iterator, Optional, Sequence, Set

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper

# NOTE: DynamoDB supports up to 38 digits precision
# Therefore, this ensures our Decimal follows what's stored in the table
DYNAMODB_CONTEXT = Context(
    Emin=-128,
    Emax=126,
    prec=38,
    traps=[Clamped, Overflow, Inexact, Rounded, Underflow],
)


class TypeDeserializer:
    """
    Deserializes DynamoDB types to Python types.

    It's based on boto3's [DynamoDB TypeDeserializer](https://boto3.amazonaws.com/v1/documentation/api/latest/_modules/boto3/dynamodb/types.html).

    The only notable difference is that for Binary (`B`, `BS`) values we return Python Bytes directly,
    since we don't support Python 2.
    """

    def deserialize(self, value: Dict) -> Any:
        """Deserialize DynamoDB data types into Python types.

        Parameters
        ----------
        value: Any
            DynamoDB value to be deserialized to a python type


            Here are the various conversions:

            DynamoDB                                Python
            --------                                ------
            {'NULL': True}                          None
            {'BOOL': True/False}                    True/False
            {'N': Decimal(value)}                   Decimal(value)
            {'S': string}                           string
            {'B': bytes}                            bytes
            {'NS': [str(value)]}                    set([str(value)])
            {'SS': [string]}                        set([string])
            {'BS': [bytes]}                         set([bytes])
            {'L': list}                             list
            {'M': dict}                             dict

        Parameters
        ----------
        value: Any
            DynamoDB value to be deserialized to a python type

        Returns
        --------
        any
            Python native type converted from DynamoDB type
        """

        dynamodb_type = list(value.keys())[0]
        deserializer: Optional[Callable] = getattr(self, f"_deserialize_{dynamodb_type}".lower(), None)
        if deserializer is None:
            raise TypeError(f"Dynamodb type {dynamodb_type} is not supported")

        return deserializer(value[dynamodb_type])

    def _deserialize_null(self, value: bool) -> None:
        return None

    def _deserialize_bool(self, value: bool) -> bool:
        return value

    def _deserialize_n(self, value: str) -> Decimal:
        # value is None or "."? It's zero
        # then return early
        value = value.lstrip("0")
        if not value or value == ".":
            return DYNAMODB_CONTEXT.create_decimal(0)

        if len(value) > 38:
            # See: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.NamingRulesDataTypes.html#HowItWorks.DataTypes.Number
            # Calculate the number of trailing zeros after the 38th character
            tail = len(value[38:]) - len(value[38:].rstrip("0"))
            # Trim the value: remove trailing zeros if any, or just take the first 38 characters
            value = value[:-tail] if tail > 0 else value[:38]

        return DYNAMODB_CONTEXT.create_decimal(value)

    def _deserialize_s(self, value: str) -> str:
        return value

    def _deserialize_b(self, value: bytes) -> bytes:
        return value

    def _deserialize_ns(self, value: Sequence[str]) -> Set[Decimal]:
        return set(map(self._deserialize_n, value))

    def _deserialize_ss(self, value: Sequence[str]) -> Set[str]:
        return set(map(self._deserialize_s, value))

    def _deserialize_bs(self, value: Sequence[bytes]) -> Set[bytes]:
        return set(map(self._deserialize_b, value))

    def _deserialize_l(self, value: Sequence[Dict]) -> Sequence[Any]:
        return [self.deserialize(v) for v in value]

    def _deserialize_m(self, value: Dict) -> Dict:
        return {k: self.deserialize(v) for k, v in value.items()}


class StreamViewType(Enum):
    """The type of data from the modified DynamoDB item that was captured in this stream record"""

    KEYS_ONLY = 0  # only the key attributes of the modified item
    NEW_IMAGE = 1  # the entire item, as it appeared after it was modified.
    OLD_IMAGE = 2  # the entire item, as it appeared before it was modified.
    NEW_AND_OLD_IMAGES = 3  # both the new and the old item images of the item.


class StreamRecord(DictWrapper):
    _deserializer = TypeDeserializer()

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
        """Deserialize DynamoDB records available in `Keys`, `NewImage`, and `OldImage`

        Parameters
        ----------
        key : str
            DynamoDB key (e.g., Keys, NewImage, or OldImage)

        Returns
        -------
        Optional[Dict[str, Any]]
            Deserialized records in Python native types
        """
        dynamodb_dict = self._data.get(key)
        if dynamodb_dict is None:
            return None

        return {k: self._deserializer.deserialize(v) for k, v in dynamodb_dict.items()}

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
