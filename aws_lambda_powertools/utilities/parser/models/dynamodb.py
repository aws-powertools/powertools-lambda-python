# ruff: noqa: FA100
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Type, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from aws_lambda_powertools.shared.dynamodb_deserializer import TypeDeserializer

_DESERIALIZER = TypeDeserializer()


class DynamoDBStreamChangedRecordModel(BaseModel):
    ApproximateCreationDateTime: Optional[datetime] = Field(  # AWS sends this as Unix epoch float
        default=None,
        description="The approximate date and time when the stream record was created (Unix epoch time).",
        examples=[1693997155.0],
    )
    Keys: Dict[str, Any] = Field(description="Primary key attributes for the item.", examples=[{"Id": {"N": "101"}}])
    NewImage: Optional[Union[Dict[str, Any], Type[BaseModel], BaseModel]] = Field(
        default=None,
        description="The item after modifications, in DynamoDB attribute-value format.",
        examples=[{"Message": {"S": "New item!"}, "Id": {"N": "101"}}],
    )
    OldImage: Optional[Union[Dict[str, Any], Type[BaseModel], BaseModel]] = Field(
        default=None,
        description="The item before modifications, in DynamoDB attribute-value format.",
        examples=[{"Message": {"S": "Old item!"}, "Id": {"N": "100"}}],
    )
    SequenceNumber: str = Field(description="A unique identifier for the stream record.", examples=["222"])
    SizeBytes: int = Field(description="The size of the stream record, in bytes.", examples=[26])
    StreamViewType: Literal["NEW_AND_OLD_IMAGES", "KEYS_ONLY", "NEW_IMAGE", "OLD_IMAGE"] = Field(
        description="The type of data included in the stream record.",
        examples=["NEW_AND_OLD_IMAGES"],
    )

    @field_validator("Keys", "NewImage", "OldImage", mode="before")
    def deserialize_field(cls, value):
        return {k: _DESERIALIZER.deserialize(v) for k, v in value.items()}


class UserIdentity(BaseModel):
    type: Literal["Service"] = Field(
        description="The type of identity that made the request, which is always 'Service' for DynamoDB streams.",
        examples=["Service"],
    )
    principalId: Literal["dynamodb.amazonaws.com"] = Field(
        description="The unique identifier for the principal that made the request.",
        examples=["dynamodb.amazonaws.com"],
    )


class DynamoDBStreamRecordModel(BaseModel):
    eventID: str = Field(description="A unique identifier for the event.", examples=["1"])
    eventName: Literal["INSERT", "MODIFY", "REMOVE"] = Field(
        description="The type of operation that was performed on the item.",
        examples=["INSERT"],
    )
    eventVersion: float = Field(description="The version of the stream record format.", examples=["1.0"])
    eventSource: Literal["aws:dynamodb"] = Field(
        description="The source of the event, which is always 'aws:dynamodb' for DynamoDB streams.",
        examples=["aws:dynamodb"],
    )
    awsRegion: str = Field(description="The AWS region where the stream record was generated.", examples=["us-west-2"])
    eventSourceARN: str = Field(
        description="The Amazon Resource Name (ARN) of the DynamoDB stream.",
        examples=["arn:aws:dynamodb:us-west-2:123456789012:table/ExampleTable/stream/2021-01-01T00:00:00.000"],
    )
    dynamodb: DynamoDBStreamChangedRecordModel = Field(
        description="Contains the details of the DynamoDB stream record.",
        examples=[
            {
                "ApproximateCreationDateTime": 1693997155.0,
                "Keys": {"Id": {"N": "101"}},
                "NewImage": {"Message": {"S": "New item!"}, "Id": {"N": "101"}},
                "OldImage": {"Message": {"S": "Old item!"}, "Id": {"N": "100"}},
                "SequenceNumber": "222",
                "SizeBytes": 26,
                "StreamViewType": "NEW_AND_OLD_IMAGES",
            },
        ],
    )
    userIdentity: Optional[UserIdentity] = Field(
        default=None,
        description="Information about the identity that made the request.",
        examples=[{"type": "Service", "principalId": "dynamodb.amazonaws.com"}],
    )


class DynamoDBStreamModel(BaseModel):
    Records: List[DynamoDBStreamRecordModel] = Field(
        description="A list of records that contain the details of the DynamoDB stream events.",
        examples=[
            {
                "eventID": "1",
                "eventName": "INSERT",
                "eventVersion": "1.0",
                "eventSource": "aws:dynamodb",
                "awsRegion": "us-west-2",
                "eventSourceARN": "arn:aws:dynamodb:us-west-2:123456789012:table/ExampleTable/stream/2021-01-01T00:00:00.000",  # noqa E501
                "dynamodb": {
                    "ApproximateCreationDateTime": 1693997155.0,
                    "Keys": {"Id": {"N": "101"}},
                    "NewImage": {"Message": {"S": "New item!"}, "Id": {"N": "101"}},
                    "OldImage": {"Message": {"S": "Old item!"}, "Id": {"N": "100"}},
                    "SequenceNumber": "222",
                    "SizeBytes": 26,
                    "StreamViewType": "NEW_AND_OLD_IMAGES",
                },
                "userIdentity": {"type": "Service", "principalId": "dynamodb.amazonaws.com"},
            },
        ],
    )


class DDBStreamBatchInfo(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    approximate_arrival_of_first_record: datetime = Field(
        description="The approximate date and time when the first stream record from the batch was created"
        ", in ISO-8601 format.",
        examples=["1970-01-01T00:00:00.000Z"],
    )
    approximate_arrival_of_last_record: datetime = Field(
        description="The approximate date and time when the last stream record from the batch was created"
        ", in ISO-8601 format.",
        examples=["1970-01-01T00:00:00.000Z"],
    )
    batch_size: int = Field(
        description="The size of the batch.",
        examples=[1],
    )
    end_sequence_number: str = Field(
        description="The unique identifier of the last stream record from the batch.",
        examples=["222"],
    )
    shard_id: str = Field(
        description="The unique identifier of the DynamoDB Stream shard that contains the records from the batch.",
        examples=["shardId-00000000000000000000-00000000"],
    )
    start_sequence_number: str = Field(
        description="The unique identifier of the first stream record from the batch.",
        examples=["222"],
    )
    stream_arn: str = Field(
        description="The Amazon Resource Name (ARN) of the DynamoDB stream.",
        examples=["arn:aws:dynamodb:us-west-2:123456789012:table/ExampleTable/stream/2021-01-01T00:00:00.000"],
    )


class RequestContext(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    approximate_invoke_count: int = Field(
        description="The number of Lambda invocations for the record.",
        examples=[1],
    )
    condition: str = Field(
        description="The condition that caused the record to be discarded.",
        examples=["RetryAttemptsExhausted"],
    )
    function_arn: str = Field(
        description="The Amazon Resource Name (ARN) of the Lambda.",
        examples=["arn:aws:lambda:eu-west-1:809313241:function:test"],
    )
    request_id: str = Field(
        description="The unique identifier of the request.",
    )


class ResponseContext(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    executed_version: str = Field(
        description="The version of the Lambda executed",
        examples=["$LATEST"],
    )
    function_error: str = Field(
        description="",
        examples=["Unhandled"],
    )
    status_code: int = Field(
        description="The status code returned by the Lambda",
    )


# https://docs.aws.amazon.com/lambda/latest/dg/services-dynamodb-errors.html
class DynamoDBStreamLambdaOnFailureDestinationModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    ddb_stream_batch_info: DDBStreamBatchInfo = Field(alias="DDBStreamBatchInfo")
    request_context: RequestContext
    response_context: ResponseContext
    timestamp: datetime = Field(
        description="The record time, in ISO-8601 format.",
        examples=["1970-01-01T00:00:00.000Z"],
    )
    version: str = Field(
        description="The version of the record format.",
        examples=["1.0"],
    )
