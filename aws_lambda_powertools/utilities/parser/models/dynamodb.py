from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel

from aws_lambda_powertools.shared.dynamodb_deserializer import TypeDeserializer
from aws_lambda_powertools.utilities.parser.types import Literal


class DynamoDBStreamChangedRecordModel(BaseModel):
    _deserializer = TypeDeserializer()

    ApproximateCreationDateTime: Optional[datetime] = None
    Keys: Dict[str, Dict[str, Any]]
    NewImage: Optional[Union[Dict[str, Any], Type[BaseModel], BaseModel]] = None
    OldImage: Optional[Union[Dict[str, Any], Type[BaseModel], BaseModel]] = None
    SequenceNumber: str
    SizeBytes: int
    StreamViewType: Literal["NEW_AND_OLD_IMAGES", "KEYS_ONLY", "NEW_IMAGE", "OLD_IMAGE"]

    # context on why it's commented: https://github.com/aws-powertools/powertools-lambda-python/pull/118
    # since both images are optional, they can both be None. However, at least one must
    # exist in a legal model of NEW_AND_OLD_IMAGES type
    # @root_validator
    # def check_one_image_exists(cls, values): # noqa: ERA001
    #     new_img, old_img = values.get("NewImage"), values.get("OldImage") # noqa: ERA001
    #     stream_type = values.get("StreamViewType") # noqa: ERA001
    #     if stream_type == "NEW_AND_OLD_IMAGES" and not new_img and not old_img: # noqa: ERA001
    #         raise TypeError("DynamoDB streams model failed validation, missing both new & old stream images") # noqa: ERA001,E501
    #     return values # noqa: ERA001

    def __init__(self, **data: Any):
        """StreamRecord constructor
        Parameters
        ----------
        data: Dict[str, Any]
            Represents the dynamodb dict inside DynamoDBStreamEvent's records
        """
        super().__init__(**data)
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
        dynamodb_dict = getattr(self, key)
        if dynamodb_dict is None:
            return None

        return {k: self._deserializer.deserialize(v) for k, v in dynamodb_dict.items()}

    @property
    def approximate_creation_date_time(self) -> Optional[datetime]:
        """The approximate date and time when the stream record was created, in UNIX epoch time format."""
        item = self.ApproximateCreationDateTime
        return None if item is None else item

    @property
    def keys(self) -> Optional[Dict[str, Any]]:
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
        return self.SequenceNumber

    @property
    def size_bytes(self) -> Optional[int]:
        """The size of the stream record, in bytes."""
        item = self.SizeBytes
        return None if item is None else int(item)


class UserIdentity(BaseModel):
    type: Literal["Service"]  # noqa: VNE003, A003
    principalId: Literal["dynamodb.amazonaws.com"]


class DynamoDBStreamRecordModel(BaseModel):
    eventID: str
    eventName: Literal["INSERT", "MODIFY", "REMOVE"]
    eventVersion: float
    eventSource: Literal["aws:dynamodb"]
    awsRegion: str
    eventSourceARN: str
    dynamodb: DynamoDBStreamChangedRecordModel
    userIdentity: Optional[UserIdentity] = None


class DynamoDBStreamModel(BaseModel):
    Records: List[DynamoDBStreamRecordModel]
