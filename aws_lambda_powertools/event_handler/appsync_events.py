from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from aws_lambda_powertools.event_handler.events_appsync._registry import ResolverEventsRegistry

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.data_classes.appsync_resolver_events_event import AppSyncResolverEventsEvent
    from aws_lambda_powertools.utilities.typing.lambda_context import LambdaContext


class AppSyncEventsResolver:
    """
    AppSync Events API Resolver
    """

    def __init__(self):
        self.context = {}  # early init as customers might add context before event resolution
        self._publish_registry = ResolverEventsRegistry()
        self._async_publish_registry = ResolverEventsRegistry()
        self._subscribe_registry = ResolverEventsRegistry()
        self._async_subscribe_registry = ResolverEventsRegistry()

    def resolve(
        self,
        event: AppSyncResolverEventsEvent,
        context: LambdaContext,
    ) -> Any:
        """Resolves the response based on the provide event and decorator operation and namespaces"""
        print(self._publish_registry.__dict__)

    def publish(
        self,
        path: str = "/default/*",
        aggregate: bool = True,
    ) -> Callable:
        return self._publish_registry.register(path=path, aggregate=aggregate)

    def async_publish(
        self,
        path: str = "/default/*",
        aggregate: bool = True,
    ) -> Callable:
        return self._async_publish_registry.register(path=path, aggregate=aggregate)

    def subscribe(
        self,
        path: str = "/default/*",
    ) -> Callable:
        return self._subscribe_registry.register(path=path)

    def async_subscribe(
        self,
        path: str = "/default/*",
    ) -> Callable:
        return self._async_subscribe_registry.register(path=path)
