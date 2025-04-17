from __future__ import annotations

import asyncio
import logging
import warnings
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.event_handler.events_appsync.exceptions import UnauthorizedException
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
    AppSync Events API Resolver for handling publish and subscribe operations.

    This class extends the Router to process AppSync real-time API events, managing
    both synchronous and asynchronous resolvers for event publishing and subscribing.

    Attributes
    ----------
    context: dict
        Dictionary to store context information accessible across resolvers
    lambda_context: LambdaContext
        Lambda context from the AWS Lambda function
    current_event: AppSyncResolverEventsEvent
        Current event being processed

    Examples
    --------
    Define a simple AppSync events resolver for a chat application:

    >>> from aws_lambda_powertools.event_handler import AppSyncEventsResolver
    >>> app = AppSyncEventsResolver()
    >>>
    >>> # Using aggregate mode to process multiple messages at once
    >>> @app.on_publish(channel_path="/default/*", aggregate=True)
    >>> def handle_batch_messages(payload):
    >>>     processed_messages = []
    >>>     for message in payload:
    >>>         # Process each message
    >>>         processed_messages.append({
    >>>             "messageId": f"msg-{message.get('id')}",
    >>>             "processed": True
    >>>         })
    >>>     return processed_messages
    >>>
    >>> # Asynchronous resolver
    >>> @app.async_on_publish(channel_path="/default/*")
    >>> async def handle_async_messages(event):
    >>>     # Perform async operations (e.g., DB queries, HTTP calls)
    >>>     await asyncio.sleep(0.1)  # Simulate async work
    >>>     return {
    >>>         "messageId": f"async-{event.get('id')}",
    >>>         "processed": True
    >>>     }
    >>>
    >>> # Lambda handler
    >>> def lambda_handler(event, context):
    >>>     return events.resolve(event, context)
    """

    def __init__(self):
        """Initialize the AppSyncEventsResolver."""
        super().__init__()
        self.context = {}  # early init as customers might add context before event resolution
        self._exception_handlers: dict[type, Callable] = {}

    def __call__(
        self,
        event: dict | AppSyncResolverEventsEvent,
        context: LambdaContext,
    ) -> Any:
        """
        Implicit lambda handler which internally calls `resolve`.

        Parameters
        ----------
        event: dict or AppSyncResolverEventsEvent
            The AppSync event to process
        context: LambdaContext
            The Lambda context

        Returns
        -------
        Any
            The resolver's response
        """
        return self.resolve(event, context)

    def resolve(
        self,
        event: dict | AppSyncResolverEventsEvent,
        context: LambdaContext,
    ) -> Any:
        """
        Resolves the response based on the provided event and decorator operation.

        Parameters
        ----------
        event: dict or AppSyncResolverEventsEvent
            The AppSync event to process
        context: LambdaContext
            The Lambda context

        Returns
        -------
        Any
            The resolver's response based on the operation type

        Examples
        --------
        >>> events = AppSyncEventsResolver()
        >>>
        >>> # Explicit call to resolve in Lambda handler
        >>> def lambda_handler(event, context):
        >>>     return events.resolve(event, context)
        """

        self._setup_context(event, context)

        if self.current_event.info.operation == "PUBLISH":
            response = self._publish_events(payload=self.current_event.events)
        else:
            response = self._subscribe_events()

        self.clear_context()

        return response

    def _subscribe_events(self) -> Any:
        """
        Handle subscribe events.

        Returns
        -------
        Any
            Any response
        """
        channel_path = self.current_event.info.channel_path
        logger.debug(f"Processing subscribe events for path {channel_path}")

        resolver = self._subscribe_registry.find_resolver(channel_path)
        if resolver:
            try:
                resolver["func"]()
                return None  # Must return None in subscribe events
            except UnauthorizedException:
                raise
            except Exception as error:
                return {"error": self._format_error_response(error)}

        self._warn_no_resolver("subscribe", channel_path)
        return None

    def _publish_events(self, payload: list[dict[str, Any]]) -> list[dict[str, Any]] | dict[str, Any]:
        """
        Handle publish events.

        Parameters
        ----------
        payload: list[dict[str, Any]]
            The events payload to process

        Returns
        -------
        list[dict[str, Any]] or dict[str, Any]
            Processed events or error response
        """

        channel_path = self.current_event.info.channel_path

        logger.debug(f"Processing publish events for path {channel_path}")

        resolver = self._publish_registry.find_resolver(channel_path)
        async_resolver = self._async_publish_registry.find_resolver(channel_path)

        if resolver and async_resolver:
            warnings.warn(
                f"Both synchronous and asynchronous resolvers found for the same event and field."
                f"The synchronous resolver takes precedence. Executing: {resolver['func'].__name__}",
                stacklevel=2,
                category=PowertoolsUserWarning,
            )

        if resolver:
            logger.debug(f"Found sync resolver: {resolver}")
            return self._process_publish_event_sync_resolver(resolver)

        if async_resolver:
            logger.debug(f"Found async resolver: {async_resolver}")
            return asyncio.run(self._call_publish_event_async_resolver(async_resolver))

        # No resolver found
        # Warning and returning AS IS
        self._warn_no_resolver("publish", channel_path, return_as_is=True)
        return {"events": payload}

    def _process_publish_event_sync_resolver(
        self,
        resolver: ResolverTypeDef,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """
        Process events using a synchronous resolver.

        Parameters
        ----------
        resolver : ResolverTypeDef
            The resolver to use for processing events

        Returns
        -------
        list[dict[str, Any]] or dict[str, Any]
            Processed events or error response

        Notes
        -----
        If the resolver is configured with aggregate=True, all events are processed
        as a batch. Otherwise, each event is processed individually.
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

                return {"events": response}
            except UnauthorizedException:
                raise
            except Exception as error:
                return {"error": self._format_error_response(error)}

        # By default, we gracefully append `None` for any records that failed processing
        results = []
        for idx, event in enumerate(self.current_event.events):
            try:
                result_return = resolver["func"](payload=event.get("payload"))
                results.append({"id": event.get("id"), "payload": result_return})
            except Exception as error:
                logger.debug(f"Failed to process event number {idx}")
                error_return = {"id": event.get("id"), "error": self._format_error_response(error)}
                results.append(error_return)

        return {"events": results}

    async def _call_publish_event_async_resolver(
        self,
        resolver: ResolverTypeDef,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """
        Process events using an asynchronous resolver.

        Parameters
        ----------
        resolver: ResolverTypeDef
            The async resolver to use for processing events

        Returns
        -------
        list[Any]
            Processed events or error responses

        Notes
        -----
        If the resolver is configured with aggregate=True, all events are processed
        as a batch. Otherwise, each event is processed individually and in parallel.
        """

        # Checks whether the entire batch should be processed at once
        if resolver["aggregate"]:
            try:
                # Process the entire batch
                response = await resolver["func"](payload=self.current_event.events)
                if not isinstance(response, list):
                    warnings.warn(
                        "Response must be a list when using aggregate, AppSync will drop those events.",
                        stacklevel=2,
                        category=PowertoolsUserWarning,
                    )

                return {"events": response}
            except UnauthorizedException:
                raise
            except Exception as error:
                return {"error": self._format_error_response(error)}

        response_async: list = []

        # Prime coroutines
        tasks = [resolver["func"](payload=e.get("payload")) for e in self.current_event.events]

        # Aggregate results and exceptions, then filter them out
        # Use `None` upon exception for graceful error handling at GraphQL engine level
        #
        # NOTE: asyncio.gather(return_exceptions=True) catches and includes exceptions in the results
        #       this will become useful when we support exception handling in AppSync resolver
        # Aggregate results and exceptions, then filter them out
        results = await asyncio.gather(*tasks, return_exceptions=True)
        response_async.extend(
            [
                (
                    {"id": e.get("id"), "error": self._format_error_response(ret)}
                    if isinstance(ret, Exception)
                    else {"id": e.get("id"), "payload": ret}
                )
                for e, ret in zip(self.current_event.events, results)
            ],
        )

        return {"events": response_async}

    def include_router(self, router: Router) -> None:
        """
        Add all resolvers defined in a router to this resolver.

        Parameters
        ----------
        router : Router
            A router containing resolvers to include

        Examples
        --------
        >>> # Create main resolver and a router
        >>> app = AppSyncEventsResolver()
        >>> router = Router()
        >>>
        >>> # Define resolvers in the router
        >>> @router.publish(path="/chat/message")
        >>> def handle_chat_message(payload):
        >>>     return {"processed": True, "messageId": payload.get("id")}
        >>>
        >>> # Include the router in the main resolver
        >>> app.include_router(chat_router)
        >>>
        >>> # Now events can handle "/chat/message" channel_path
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

    def _format_error_response(self, error=None) -> str:
        """
        Format error responses consistently.

        Parameters
        ----------
        error: Exception or None
            The error to format

        Returns
        -------
        str
            Formatted error message
        """
        if isinstance(error, Exception):
            return f"{error.__class__.__name__} - {str(error)}"
        return "An unknown error occurred"

    def _warn_no_resolver(self, operation_type: str, path: str, return_as_is: bool = False) -> None:
        """
        Generate consistent warning messages for missing resolvers.

        Parameters
        ----------
        operation_type : str
            Type of operation (e.g., "publish", "subscribe")
        path : str
            The channel path that's missing a resolver
        return_as_is : bool, optional
            Whether payload will be returned as is, by default False
        """
        message = (
            f"No resolvers were found for {operation_type} operations with path {path}"
            f"{'. We will return the entire payload as is' if return_as_is else ''}"
        )
        warnings.warn(message, stacklevel=3, category=PowertoolsUserWarning)

    def _setup_context(self, event: dict | AppSyncResolverEventsEvent, context: LambdaContext) -> None:
        """
        Set up the context and event for processing.

        Parameters
        ----------
        event : dict or AppSyncResolverEventsEvent
            The AppSync event to process
        context : LambdaContext
            The Lambda context
        """
        self.lambda_context = context
        Router.lambda_context = context

        Router.current_event = (
            event if isinstance(event, AppSyncResolverEventsEvent) else AppSyncResolverEventsEvent(event)
        )
        self.current_event = Router.current_event
