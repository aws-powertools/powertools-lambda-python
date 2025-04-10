from __future__ import annotations

import asyncio
import logging
import warnings
from typing import TYPE_CHECKING, Any, Callable

from aws_lambda_powertools.event_handler.events_appsync.router import Router
from aws_lambda_powertools.utilities.data_classes.appsync_resolver_events_event import AppSyncResolverEventsEvent
from aws_lambda_powertools.warnings import PowertoolsUserWarning

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
            return self._call_publish_events(payload=self.current_event.events)

        response = self._call_subscribe_events()

        self.clear_context()

        return response

    def _call_subscribe_events(self) -> Any:
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

    def _call_publish_events(self, payload: list[dict[str, Any]]) -> Any:
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
            return self._call_publish_event_sync_resolver(
                resolver=resolver["func"],
                aggregate=resolver["aggregate"],
            )

        if async_resolver:
            logger.debug(f"Found async resolver. {resolver}")
            return asyncio.run(
                self._call_publish_event_async_resolver(
                    resolver=async_resolver["func"],
                    aggregate=async_resolver["aggregate"],
                ),
            )

        # No resolver found
        # Warning and returning AS IS
        warnings.warn(
            f"No resolvers were found for publish operations with path {self.current_event.info.channel_path}",
            stacklevel=2,
            category=PowertoolsUserWarning)

        return {"events": payload}

    def _call_publish_event_sync_resolver(
        self,
        resolver: Callable,
        aggregate: bool = True,
    ) -> list[Any]:
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
        if aggregate:
            # Process the entire batch
            response = resolver(payload=self.current_event.events)

            if not isinstance(response, list):
                warnings.warn(
                    "Response must be a list when using aggregate, AppSync will drop those events.",
                    stacklevel=2,
                    category=PowertoolsUserWarning)

            return response


        # By default, we gracefully append `None` for any records that failed processing
        results = []
        for idx, event in enumerate(self.current_event.events):
            try:
                results.append(resolver(payload=event))
            except Exception:
                logger.debug(f"Failed to process event number {idx}")
                results.append(None)

        return results

    async def _call_publish_event_async_resolver(
        self,
        resolver: Callable,
        aggregate: bool = True,
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
        if aggregate:
            # Process the entire batch
            response = await resolver(event=self.current_batch_event)
            if not isinstance(response, list):
                warnings.warn(
                    "Response must be a list when using aggregate, AppSync will drop those events.",
                    stacklevel=2,
                    category=PowertoolsUserWarning)

            return response

        response: list = []

        # Prime coroutines
        tasks = [resolver(event=e, **e.arguments) for e in self.current_batch_event]

        # Aggregate results and exceptions, then filter them out
        # Use `None` upon exception for graceful error handling at GraphQL engine level
        #
        # NOTE: asyncio.gather(return_exceptions=True) catches and includes exceptions in the results
        #       this will become useful when we support exception handling in AppSync resolver
        results = await asyncio.gather(*tasks, return_exceptions=True)
        response.extend(None if isinstance(ret, Exception) else ret for ret in results)

        return response
