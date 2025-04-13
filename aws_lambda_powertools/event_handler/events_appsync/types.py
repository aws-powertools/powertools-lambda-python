from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterator, TypedDict

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper

if TYPE_CHECKING:
    from collections.abc import Callable


class ResolverTypeDef(TypedDict):
    """
    Type definition for resolver dictionary

    Parameters
    ----------
    func: Callable[..., Any]
        Resolver function
    aggregate: bool
        Aggregation flag or method
    """

    func: Callable[..., Any]
    aggregate: bool


class AppSyncEventsPayloadDict(DictWrapper):
    @property
    def id(self) -> str:
        return self["id"]

    @property
    def payload(self) -> dict[str, Any]:
        return self["payload"]


class AppSyncEventsPayloadList(DictWrapper):
    @property
    def records(self) -> Iterator[AppSyncEventsPayloadDict]:
        for record in self:
            yield AppSyncEventsPayloadDict(data=record)
