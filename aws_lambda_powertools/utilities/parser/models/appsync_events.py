from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser.models.appsync import AppSyncIdentity, AppSyncRequestModel


class AppSyncEventsInfoChannelModel(BaseModel):
    path: str
    segments: List[str]


class AppSyncEventsInfoChannelNamespaceModel(BaseModel):
    name: str


class AppSyncEventsInfoModel(BaseModel):
    channel: AppSyncEventsInfoChannelModel
    channelNamespace: AppSyncEventsInfoChannelNamespaceModel
    operation: Literal["PUBLISH", "SUBSCRIBE"]


class AppSyncEventsEventModel(BaseModel):
    id: str
    payload: Dict[str, Any]


class AppSyncEventsModel(BaseModel):
    identity: Optional[AppSyncIdentity] = None
    request: AppSyncRequestModel
    info: AppSyncEventsInfoModel
    prev: Optional[str] = None
    outErrors: Optional[List[str]] = None
    stash: Optional[Dict[str, Any]] = None
    events: Optional[List[AppSyncEventsEventModel]] = None
