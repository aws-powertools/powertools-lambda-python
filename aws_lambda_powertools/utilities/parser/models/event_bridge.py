from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aws_lambda_powertools.utilities.parser.types import RawDictOrModel


class EventBridgeModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    version: str = Field(description="By default, this is set to 0 (zero) in all events.", examples=["0"])
    id: str = Field(  # noqa: A003,VNE003
        description="A Version 4 UUID generated for every event.",
        examples=["6a7e8feb-b491-4cf7-a9f1-bf3703467718"],
    )
    source: str = Field(
        description="Identifies the service that sourced the event. \
        All events sourced from within AWS begin with 'aws.'",
        examples=["aws.ec2", "aws.s3", "aws.events", "aws.scheduler"],
    )
    account: str = Field(
        description="The 12-digit AWS account ID of the owner of the service emitting the event.",
        examples=["111122223333", "123456789012"],
    )
    time: datetime = Field(
        description="The event timestamp, which can be specified by the service originating the event.",
        examples=["2017-12-22T18:43:48Z", "2023-01-15T10:30:00Z"],
    )
    region: str = Field(
        description="Identifies the AWS region where the event originated.",
        examples=["us-east-1", "us-west-2", "eu-west-1"],
    )
    resources: List[str] = Field(
        description="A JSON array that contains ARNs that identify resources involved in the event. "
        "Inclusion of these ARNs is at the discretion of the service.",
        examples=[
            ["arn:aws:ec2:us-west-1:123456789012:instance/i-1234567890abcdef0"],
            ["arn:aws:s3:::my-bucket/my-key"],
            ["arn:aws:events:us-east-1:123456789012:rule/MyRule"],
        ],
    )
    detail_type: str = Field(
        ...,
        alias="detail-type",
        description="Identifies, in combination with the source field, \
        the fields and values that appear in the detail field.",
        examples=["EC2 Instance State-change Notification", "Object Created", "Scheduled Event"],
    )
    detail: RawDictOrModel = Field(
        description="A JSON object, whose content is at the discretion of the service originating the event.",
    )
    replay_name: Optional[str] = Field(
        None,
        alias="replay-name",
        description="Identifies whether the event is being replayed and what is the name of the replay.",
        examples=["replay_archive", "my-replay-2023"],
    )

    @field_validator("detail", mode="before")
    def validate_detail(cls, v, fields):
        # EventBridge Scheduler sends detail field as '{}' string when no payload is present
        # See: https://github.com/aws-powertools/powertools-lambda-python/issues/6112
        return {} if fields.data.get("source") == "aws.scheduler" and v == "{}" else v
