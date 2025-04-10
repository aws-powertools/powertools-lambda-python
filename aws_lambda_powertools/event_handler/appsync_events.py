from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable

from aws_lambda_powertools.event_handler.events_appsync.router import Router
from aws_lambda_powertools.utilities.data_classes.appsync_resolver_events_event import AppSyncResolverEventsEvent

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing.lambda_context import LambdaContext

logger = logging.getLogger(__name__)
class AppSyncEventsResolver(Router):
    """
    AppSync Events API Resolver
    """

    def __init__(self):
        super().__init__()
        self.context = {}  # early init as customers might add context before event resolution
        self._exception_handlers: dict[type, Callable] = {}

    def __call__(
        self,
        event: dict,
        context: LambdaContext,
    ) -> Any:
        """Implicit lambda handler which internally calls `resolve`"""
        return self.resolve(event, context)

    def resolve(
        self,
        event: AppSyncResolverEventsEvent,
        context: LambdaContext,
    ) -> Any:
        """Resolves the response based on the provide event and decorator operation and namespaces"""

        self.lambda_context = context
        Router.lambda_context = context

        Router.current_event = AppSyncResolverEventsEvent(event)
        self.current_event = Router.current_event

        if self.current_event.info.operation == "PUBLISH":
            response = self._call_publish_events(payload=self.current_event.events)

        response = self._call_subscribe_events()

        self.clear_context()

        return response

    def _call_subscribe_events(self) -> Any:
        # PLACEHOLDER
        pass

    def _call_publish_events(self, payload: list[dict[str, Any]]) -> Any:
        """Call single event resolver

        Parameters
        ----------
        event : dict
            Event
        data_model : type[AppSyncResolverEvent]
            Data_model to decode AppSync event, by default it is of AppSyncResolverEvent type or subclass of it
        """

        result = []
        logger.debug("Processing direct resolver event")

        #self.current_event = data_model(event)
        resolver = self._publish_registry.find_resolver(self.current_event.info.channel_path)
        if not resolver:
            print(f"No resolver found for '{self.current_event.info.channel_path}'")
        print(resolver)

        if not resolver["aggregate"]:
            return resolver["func"](payload=self.current_event.events)
        else:
            for i in self.current_event.events:
                result.append(resolver["func"](payload=i))

            return result
