from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from aws_lambda_powertools.utilities.parser.models.appsync import AppSyncIdentity, AppSyncRequestModel


class AppSyncEventsInfoChannelModel(BaseModel):
    path: str = Field(
        description="The full path of the AppSync Events channel.",
        examples=["/default/channel", "/notifications/user-updates", "/chat/room-123"],
    )
    segments: List[str] = Field(
        description="The path segments of the channel, split by forward slashes.",
        examples=[["default", "channel"], ["notifications", "user-updates"], ["chat", "room-123"]],
    )


class AppSyncEventsInfoChannelNamespaceModel(BaseModel):
    name: str = Field(
        description="The namespace name for the AppSync Events channel.",
        examples=["default", "notifications", "chat", "user-events"],
    )


class AppSyncEventsInfoModel(BaseModel):
    channel: AppSyncEventsInfoChannelModel = Field(description="Information about the AppSync Events channel.")
    channelNamespace: AppSyncEventsInfoChannelNamespaceModel = Field(
        description="The namespace information for the channel.",
    )
    operation: Literal["PUBLISH", "SUBSCRIBE"] = Field(
        description="The type of operation being performed on the channel.",
        examples=["PUBLISH", "SUBSCRIBE"],
    )


class AppSyncEventsEventModel(BaseModel):
    id: str = Field(
        description="The unique identifier for the event.",
        examples=["1", "2", "event-123", "notification-456"],
    )
    payload: Dict[str, Any] = Field(
        description="The event data payload containing the actual event information.",
        examples=[
            {"event_1": "data_1"},
            {"event_2": "data_2"},
            {"userId": "123", "action": "login", "timestamp": "2023-01-01T00:00:00Z"},
            {"message": "Hello World", "type": "notification"},
        ],
    )


class AppSyncEventsModel(BaseModel):
    identity: Optional[AppSyncIdentity] = Field(
        default=None,
        description="Information about the caller identity (authenticated user or API key).",
    )
    request: AppSyncRequestModel = Field(description="Information about the GraphQL request context.")
    info: AppSyncEventsInfoModel = Field(
        description="Information about the AppSync Events operation including channel details.",
    )
    prev: Optional[str] = Field(
        default=None,
        description="Results from the previous operation in a pipeline resolver.",
        examples=["previous-result-data"],
    )
    outErrors: Optional[List[str]] = Field(
        default=None,
        description="List of output errors that occurred during event processing.",
        examples=[["Error message 1", "Error message 2"]],
    )
    stash: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "The stash is a map that is made available inside each resolver and function mapping template. "
            "The same stash instance lives through a single resolver execution."
        ),
        examples=[{"customData": "value", "userId": "123"}],
    )
    events: Optional[List[AppSyncEventsEventModel]] = Field(
        default=None,
        description="List of events being published or subscribed to in the AppSync Events operation.",
        examples=[
            [{"id": "1", "payload": {"event_1": "data_1"}}, {"id": "2", "payload": {"event_2": "data_2"}}],
        ],
    )
