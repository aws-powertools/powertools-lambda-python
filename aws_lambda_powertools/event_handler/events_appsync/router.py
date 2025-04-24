from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.event_handler.events_appsync._registry import ResolverEventsRegistry
from aws_lambda_powertools.event_handler.events_appsync.base import DEFAULT_ROUTE, BaseRouter

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.data_classes.appsync_resolver_events_event import AppSyncResolverEventsEvent
    from aws_lambda_powertools.utilities.typing.lambda_context import LambdaContext


class Router(BaseRouter):
    """
    Router for AppSync real-time API event handling.

    This class provides decorators to register resolver functions for publish and subscribe
    operations in AppSync real-time APIs.

    Parameters
    ----------
    context : dict
        Dictionary to store context information accessible across resolvers
    current_event : AppSyncResolverEventsEvent
        Current event being processed
    lambda_context : LambdaContext
        Lambda context from the AWS Lambda function

    Examples
    --------
    Create a router and define resolvers:

    >>> chat_router = Router()
    >>>
    >>> # Register a resolver for publish operations
    >>> @chat_router.on_publish(path="/chat/message")
    >>> def handle_message(payload):
    >>>     # Process message
    >>>     return {"success": True, "messageId": payload.get("id")}
    >>>
    >>> # Register an async resolver for publish operations
    >>> @chat_router.async_on_publish(path="/chat/typing")
    >>> async def handle_typing(event):
    >>>     # Process typing indicator
    >>>     await some_async_operation()
    >>>     return {"processed": True}
    >>>
    >>> # Register a resolver for subscribe operations
    >>> @chat_router.on_subscribe(path="/chat/room/*")
    >>> def handle_subscribe(event):
    >>>     # Handle subscription setup
    >>>     return {"allowed": True}
    """

    context: dict
    current_event: AppSyncResolverEventsEvent
    lambda_context: LambdaContext

    def __init__(self):
        """
        Initialize a new Router instance.

        Sets up empty context and registry containers for different types of resolvers.
        """
        self.context = {}  # early init as customers might add context before event resolution
        self._publish_registry = ResolverEventsRegistry(kind_resolver="on_publish")
        self._async_publish_registry = ResolverEventsRegistry(kind_resolver="async_on_publish")
        self._subscribe_registry = ResolverEventsRegistry(kind_resolver="on_subscribe")

    def on_publish(
        self,
        path: str = DEFAULT_ROUTE,
        aggregate: bool = False,
    ) -> Callable:
        """
        Register a resolver function for publish operations.

        Parameters
        ----------
        path : str, optional
            The channel path pattern to match for this resolver, by default "/default/*"
        aggregate : bool, optional
            Whether to process events in aggregate (batch) mode, by default False

        Returns
        -------
        Callable
            Decorator function that registers the resolver

        Examples
        --------
        >>> router = Router()
        >>>
        >>> # Basic usage
        >>> @router.on_publish(path="/notifications/new")
        >>> def handle_notification(payload):
        >>>     # Process a single notification
        >>>     return {"processed": True, "notificationId": payload.get("id")}
        >>>
        >>> # Aggregate mode for batch processing
        >>> @router.on_publish(path="/notifications/batch", aggregate=True)
        >>> def handle_batch_notifications(payload):
        >>>     # Process multiple notifications at once
        >>>     results = []
        >>>     for item in payload:
        >>>         # Process each item
        >>>         results.append({"processed": True, "id": item.get("id")})
        >>>     return results
        """
        return self._publish_registry.register(path=path, aggregate=aggregate)

    def async_on_publish(
        self,
        path: str = DEFAULT_ROUTE,
        aggregate: bool = False,
    ) -> Callable:
        """
        Register an asynchronous resolver function for publish operations.

        Parameters
        ----------
        path : str, optional
            The channel path pattern to match for this resolver, by default "/default/*"
        aggregate : bool, optional
            Whether to process events in aggregate (batch) mode, by default False

        Returns
        -------
        Callable
            Decorator function that registers the async resolver

        Examples
        --------
        >>> router = Router()
        >>>
        >>> # Basic async usage
        >>> @router.async_on_publish(path="/messages/send")
        >>> async def handle_message(event):
        >>>     # Perform async operations
        >>>     result = await database.save_message(event)
        >>>     return {"saved": True, "messageId": result.id}
        >>>
        >>> # Aggregate mode for batch processing
        >>> @router.async_on_publish(path="/messages/batch", aggregate=True)
        >>> async def handle_batch_messages(events):
        >>>     # Process multiple messages asynchronously
        >>>     tasks = [database.save_message(e) for e in events]
        >>>     results = await asyncio.gather(*tasks)
        >>>     return [{"saved": True, "id": r.id} for r in results]
        """
        return self._async_publish_registry.register(path=path, aggregate=aggregate)

    def on_subscribe(
        self,
        path: str = DEFAULT_ROUTE,
    ) -> Callable:
        """
        Register a resolver function for subscribe operations.

        Parameters
        ----------
        path : str, optional
            The channel path pattern to match for this resolver, by default "/default/*"

        Returns
        -------
        Callable
            Decorator function that registers the resolver

        Examples
        --------
        >>> router = Router()
        >>>
        >>> # Handle subscription request
        >>> @router.on_subscribe(path="/chat/room/*")
        >>> def authorize_subscription(event):
        >>>     # Verify if the client can subscribe to this room
        >>>     room_id = event.info.channel_path.split('/')[-1]
        >>>     user_id = event.identity.username
        >>>
        >>>     # Check if user is allowed in this room
        >>>     is_allowed = check_permission(user_id, room_id)
        >>>
        >>>     return {
        >>>         "allowed": is_allowed,
        >>>         "roomId": room_id
        >>>     }
        """
        return self._subscribe_registry.register(path=path)

    def append_context(self, **additional_context):
        """Append key=value data as routing context"""
        self.context.update(**additional_context)

    def clear_context(self):
        """Resets routing context"""
        self.context.clear()
