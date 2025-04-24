from __future__ import annotations

from typing import Any

from aws_lambda_powertools.utilities.data_classes.appsync_resolver_event import AppSyncEventBase
from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class AppSyncResolverEventsInfo(DictWrapper):
    @property
    def channel(self) -> dict[str, Any]:
        """Channel details including path and segments"""
        return self["channel"]

    @property
    def channel_path(self) -> str:
        """Provides direct access to the 'path' attribute within the 'channel' object."""
        return self["channel"]["path"]

    @property
    def channel_segments(self) -> list[str]:
        """Provides direct access to the 'segments' attribute within the 'channel' object."""
        return self["channel"]["segments"]

    @property
    def channel_namespace(self) -> dict:
        """Namespace configuration for the channel"""
        return self["channelNamespace"]

    @property
    def operation(self) -> str:
        """The operation being performed (e.g., PUBLISH, SUBSCRIBE)"""
        return self["operation"]


class AppSyncResolverEventsEvent(AppSyncEventBase):
    """AppSync resolver event events
    Documentation:
    -------------
    - TBD
    """

    @property
    def events(self) -> list[dict[str, Any]]:
        """The payload sent to Lambda"""
        return self.get("events") or [{}]

    @property
    def out_errors(self) -> list:
        """The outErrors property"""
        return self.get("outErrors") or []

    @property
    def info(self) -> AppSyncResolverEventsInfo:
        "The info containing information about channel, namespace, and event"
        return AppSyncResolverEventsInfo(self["info"])
