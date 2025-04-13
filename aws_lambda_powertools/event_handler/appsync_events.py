from __future__ import annotations

import asyncio
import logging
import warnings
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.event_handler.events_appsync.router import Router
from aws_lambda_powertools.utilities.data_classes.appsync_resolver_events_event import AppSyncResolverEventsEvent
from aws_lambda_powertools.warnings import PowertoolsUserWarning

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.event_handler.events_appsync.types import ResolverTypeDef
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
        event: dict | AppSyncResolverEventsEvent,
        context: LambdaContext,
    ) -> Any:
        """Implicit lambda handler which internally calls `resolve`"""
        return self.resolve(event, context)

    def resolve(
        self,
        event: dict | AppSyncResolverEventsEvent,
        context: LambdaContext,
    ) -> Any:
        """Resolves the response based on the provide event and decorator operation and namespaces"""

        self.lambda_context = context
        Router.lambda_context = context

        Router.current_event = (
            event if isinstance(event, AppSyncResolverEventsEvent) else AppSyncResolverEventsEvent(event)
        )
        self.current_event = Router.current_event

        if self.current_event.info.operation == "PUBLISH":
            return self._publish_events(payload=self.current_event.events)

        response = self._subscribe_events()

        self.clear_context()

        return response

    def _subscribe_events(self) -> Any:
        logger.debug(f"Processing subscribe events for path {self.current_event.info.channel_path}")

        resolver = self._subscribe_registry.find_resolver(self.current_event.info.channel_path)
        if not resolver:
            warnings.warn(
                f"No resolvers were found for publish operations with path {self.current_event.info.channel_path}",
                stacklevel=2,
                category=PowertoolsUserWarning,
            )
            return
        pass

    def _publish_events(self, payload: list[dict[str, Any]]) -> list[dict[str, Any]] | dict[str, Any]:
        """Call single event resolver

        Parameters
        ----------
        payload : list[dict[str, Any]]
            the messages sent by AppSync
        """

        logger.debug(f"Processing publish events for path {self.current_event.info.channel_path}")

        resolver = self._publish_registry.find_resolver(self.current_event.info.channel_path)
        async_resolver = self._async_publish_registry.find_resolver(self.current_event.info.channel_path)

        if resolver and async_resolver:
            warnings.warn(
                f"Both synchronous and asynchronous resolvers found for the same event and field."
                f"The synchronous resolver takes precedence. Executing: {resolver['func'].__name__}",
                stacklevel=2,
                category=PowertoolsUserWarning,
            )

        if resolver:
            logger.debug(f"Found sync resolver. {resolver}")
            return self._process_publish_event_sync_resolver(
                resolver=resolver,
            )

        if async_resolver:
            logger.debug(f"Found async resolver. {resolver}")
            return asyncio.run(
                self._call_publish_event_async_resolver(
                    resolver=async_resolver,
                ),
            )

        # No resolver found
        # Warning and returning AS IS
        warnings.warn(
            f"No resolvers were found for publish operations with path {self.current_event.info.channel_path}"
            "We will return the entire payload as is",
            stacklevel=2,
            category=PowertoolsUserWarning,
        )

        return {"events": payload}

    def _process_publish_event_sync_resolver(
        self,
        resolver: ResolverTypeDef,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """
        Calls a synchronous batch resolver function for each event in the current batch.

        Parameters
        ----------
        resolver: Callable
            The callable function to resolve events.
        raise_on_error: bool
            A flag indicating whether to raise an error when processing batches
            with failed items. Defaults to False, which means errors are handled without raising exceptions.
        aggregate: bool
            A flag indicating whether the batch items should be processed at once or individually.
            If True (default), the batch resolver will process all items in the batch as a single event.
            If False, the batch resolver will process each item in the batch individually.

        Returns
        -------
        list[Any]
            A list of results corresponding to the resolved events.
        """

        # Checks whether the entire batch should be processed at once
        if resolver["aggregate"]:
            try:
                # Process the entire batch
                response = resolver["func"](payload=self.current_event.events)

                if not isinstance(response, list):
                    warnings.warn(
                        "Response must be a list when using aggregate, AppSync will drop those events.",
                        stacklevel=2,
                        category=PowertoolsUserWarning,
                    )

                return response
            except Exception as error:
                return {"error": self.format_error_response(error)}

        # By default, we gracefully append `None` for any records that failed processing
        results = []
        for idx, event in enumerate(self.current_event.events):
            try:
                results.append(resolver["func"](payload=event))
            except Exception as error:
                logger.debug(f"Failed to process event number {idx}")
                error_return = {"id": event.get("id"), "error": self.format_error_response(error)}
                results.append(error_return)

        return results

    async def _call_publish_event_async_resolver(
        self,
        resolver: ResolverTypeDef,
    ) -> list[Any]:
        """
        Asynchronously call a batch resolver for each event in the current batch.

        Parameters
        ----------
        resolver: Callable
            The asynchronous resolver function.
        raise_on_error: bool
            A flag indicating whether to raise an error when processing batches
            with failed items. Defaults to False, which means errors are handled without raising exceptions.
        aggregate: bool
            A flag indicating whether the batch items should be processed at once or individually.
            If True (default), the batch resolver will process all items in the batch as a single event.
            If False, the batch resolver will process each item in the batch individually.

        Returns
        -------
        list[Any]
            A list of results corresponding to the resolved events.
        """

        # Checks whether the entire batch should be processed at once
        if resolver["aggregate"]:
            # Process the entire batch
            response = await resolver["func"](event=self.current_event.events)
            if not isinstance(response, list):
                warnings.warn(
                    "Response must be a list when using aggregate, AppSync will drop those events.",
                    stacklevel=2,
                    category=PowertoolsUserWarning,
                )

            return response

        response_async: list = []

        # Prime coroutines
        tasks = [resolver["func"](event=e) for e in self.current_event.events]

        # Aggregate results and exceptions, then filter them out
        # Use `None` upon exception for graceful error handling at GraphQL engine level
        #
        # NOTE: asyncio.gather(return_exceptions=True) catches and includes exceptions in the results
        #       this will become useful when we support exception handling in AppSync resolver
        results = await asyncio.gather(*tasks, return_exceptions=True)
        response_async.extend(None if isinstance(ret, Exception) else ret for ret in results)

        return response_async

    def include_router(self, router: Router) -> None:
        """Adds all resolvers defined in a router

        Parameters
        ----------
        router : Router
            A router containing a dict of field resolvers
        """

        # Merge app and router context
        logger.debug("Merging router and app context")
        self.context.update(**router.context)

        # use pointer to allow context clearance after event is processed e.g., resolve(evt, ctx)
        router.context = self.context

        logger.debug("Merging router resolver registries")
        self._publish_registry.merge(router._publish_registry)
        self._async_publish_registry.merge(router._async_publish_registry)
        self._subscribe_registry.merge(router._subscribe_registry)

    def format_error_response(self, error=None) -> str:
        if isinstance(error, Exception):
            return f"{error.__class__.__name__} - {str(error)}"
        return "An unknown error occurred"
