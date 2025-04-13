from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from aws_lambda_powertools.event_handler.events_appsync._registry import ResolverEventsRegistry
from aws_lambda_powertools.event_handler.events_appsync.base import BaseRouter

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.data_classes.appsync_resolver_events_event import AppSyncResolverEventsEvent
    from aws_lambda_powertools.utilities.typing.lambda_context import LambdaContext


class Router(BaseRouter):

    context: dict
    current_event: AppSyncResolverEventsEvent
    lambda_context: LambdaContext

    def __init__(self):
        self.context = {}  # early init as customers might add context before event resolution
        self._publish_registry = ResolverEventsRegistry(kind_resolver="on_publish")
        self._async_publish_registry = ResolverEventsRegistry(kind_resolver="async_on_publish")
        self._subscribe_registry = ResolverEventsRegistry(kind_resolver="on_subscribe")

    def on_publish(
        self,
        path: str = "/default/*",
        aggregate: bool = False,
    ) -> Callable:
        return self._publish_registry.register(path=path, aggregate=aggregate)

    def async_on_publish(
        self,
        path: str = "/default/*",
        aggregate: bool = False,
    ) -> Callable:
        return self._async_publish_registry.register(path=path, aggregate=aggregate)

    def on_subscribe(
        self,
        path: str = "/default/*",
    ) -> Callable:
        return self._subscribe_registry.register(path=path)

    def append_context(self, **additional_context):
        """Append key=value data as routing context"""
        self.context.update(**additional_context)

    def clear_context(self):
        """Resets routing context"""
        self.context.clear()
