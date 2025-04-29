from __future__ import annotations

import asyncio
import logging
import warnings
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.event_handler.exception_handling import ExceptionHandlerManager
from aws_lambda_powertools.event_handler.graphql_appsync.exceptions import InvalidBatchResponse, ResolverNotFoundError
from aws_lambda_powertools.event_handler.graphql_appsync.router import Router
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.typing import LambdaContext

from aws_lambda_powertools.warnings import PowertoolsUserWarning

logger = logging.getLogger(__name__)


class AppSyncResolver(Router):
    """
    AppSync GraphQL API Resolver

    Example
    -------
    ```python
    from aws_lambda_powertools.event_handler import AppSyncResolver

    app = AppSyncResolver()

    @app.resolver(type_name="Query", field_name="listLocations")
    def list_locations(page: int = 0, size: int = 10) -> list:
        # Your logic to fetch locations with arguments passed in
        return [{"id": 100, "name": "Smooth Grooves"}]

    @app.resolver(type_name="Merchant", field_name="extraInfo")
    def get_extra_info() -> dict:
        # Can use "app.current_event.source" to filter within the parent context
        account_type = app.current_event.source["accountType"]
        method = "BTC" if account_type == "NEW" else "USD"
        return {"preferredPaymentMethod": method}

    @app.resolver(field_name="commonField")
    def common_field() -> str:
        # Would match all fieldNames matching 'commonField'
        return str(uuid.uuid4())
    ```
    """

    def __init__(self):
        """
        Initialize a new instance of the AppSyncResolver.
        """
        super().__init__()
        self.context = {}  # early init as customers might add context before event resolution
        self.exception_handler_manager = ExceptionHandlerManager()
        self._exception_handlers: dict[type, Callable] = {}

    def __call__(
        self,
        event: dict,
        context: LambdaContext,
        data_model: type[AppSyncResolverEvent] = AppSyncResolverEvent,
    ) -> Any:
        """Implicit lambda handler which internally calls `resolve`"""
        return self.resolve(event, context, data_model)

    def resolve(
        self,
        event: dict | list[dict],
        context: LambdaContext,
        data_model: type[AppSyncResolverEvent] = AppSyncResolverEvent,
    ) -> Any:
        """Resolves the response based on the provide event and decorator routes

        Parameters
        ----------
        event : dict | list[Dict]
            Lambda event either coming from batch processing endpoint or from standard processing endpoint
        context : LambdaContext
            Lambda context
        data_model:
            Your data data_model to decode AppSync event, by default AppSyncResolverEvent

        Example
        -------

        ```python
        from aws_lambda_powertools.event_handler import AppSyncResolver
        from aws_lambda_powertools.utilities.typing import LambdaContext

        @app.resolver(field_name="createSomething")
        def create_something(id: str):  # noqa AA03 VNE003
            return id

        def handler(event, context: LambdaContext):
            return app.resolve(event, context)
        ```

        **Bringing custom models**

        ```python
        from aws_lambda_powertools import Logger, Tracer

        from aws_lambda_powertools.logging import correlation_paths
        from aws_lambda_powertools.event_handler import AppSyncResolver

        tracer = Tracer(service="sample_resolver")
        logger = Logger(service="sample_resolver")
        app = AppSyncResolver()


        class MyCustomModel(AppSyncResolverEvent):
            @property
            def country_viewer(self) -> str:
                return self.request_headers.get("cloudfront-viewer-country", "")


        @app.resolver(field_name="listLocations")
        @app.resolver(field_name="locations")
        def get_locations(name: str, description: str = ""):
            if app.current_event.country_viewer == "US":
                ...
            return name + description


        @logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
        @tracer.capture_lambda_handler
        def lambda_handler(event, context):
            return app.resolve(event, context, data_model=MyCustomModel)
        ```

        Returns
        -------
        Any
            Returns the result of the resolver

        Raises
        -------
        ValueError
            If we could not find a field resolver
        """

        self.lambda_context = context
        Router.lambda_context = context

        try:
            if isinstance(event, list):
                Router.current_batch_event = [data_model(e) for e in event]
                response = self._call_batch_resolver(event=event, data_model=data_model)
            else:
                Router.current_event = data_model(event)
                response = self._call_single_resolver(event=event, data_model=data_model)
        except Exception as exp:
            response_builder = self.exception_handler_manager.lookup_exception_handler(type(exp))
            if response_builder:
                return response_builder(exp)
            raise

        # We don't clear the context for coroutines because we don't have control over the event loop.
        # If we clean the context immediately, it might not be available when the coroutine is actually executed.
        # For single async operations, the context should be cleaned up manually after the coroutine completes.
        # See: https://github.com/aws-powertools/powertools-lambda-python/issues/5290
        # REVIEW: Review this support in Powertools V4
        if not asyncio.iscoroutine(response):
            self.clear_context()

        return response

    def _call_single_resolver(self, event: dict, data_model: type[AppSyncResolverEvent]) -> Any:
        """Call single event resolver

        Parameters
        ----------
        event : dict
            Event
        data_model : type[AppSyncResolverEvent]
            Data_model to decode AppSync event, by default it is of AppSyncResolverEvent type or subclass of it
        """

        logger.debug("Processing direct resolver event")

        self.current_event = data_model(event)
        resolver = self._resolver_registry.find_resolver(self.current_event.type_name, self.current_event.field_name)
        if not resolver:
            raise ValueError(f"No resolver found for '{self.current_event.type_name}.{self.current_event.field_name}'")
        return resolver["func"](**self.current_event.arguments)

    def _call_sync_batch_resolver(
        self,
        resolver: Callable,
        raise_on_error: bool = False,
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

        logger.debug(f"Graceful error handling flag {raise_on_error=}")

        # Checks whether the entire batch should be processed at once
        if aggregate:
            # Process the entire batch
            response = resolver(event=self.current_batch_event)

            if not isinstance(response, list):
                raise InvalidBatchResponse("The response must be a List when using batch resolvers")

            return response

        # Non aggregated events, so we call this event list x times
        # Stop on first exception we encounter
        if raise_on_error:
            return [
                resolver(event=appconfig_event, **appconfig_event.arguments)
                for appconfig_event in self.current_batch_event
            ]

        # By default, we gracefully append `None` for any records that failed processing
        results = []
        for idx, event in enumerate(self.current_batch_event):
            try:
                results.append(resolver(event=event, **event.arguments))
            except Exception:
                logger.debug(f"Failed to process event number {idx} from field '{event.info.field_name}'")
                results.append(None)

        return results

    async def _call_async_batch_resolver(
        self,
        resolver: Callable,
        raise_on_error: bool = False,
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

        logger.debug(f"Graceful error handling flag {raise_on_error=}")

        # Checks whether the entire batch should be processed at once
        if aggregate:
            # Process the entire batch
            ret = await resolver(event=self.current_batch_event)
            if not isinstance(ret, list):
                raise InvalidBatchResponse("The response must be a List when using batch resolvers")

            return ret

        response: list = []

        # Prime coroutines
        tasks = [resolver(event=e, **e.arguments) for e in self.current_batch_event]

        # Aggregate results or raise at first error
        if raise_on_error:
            response.extend(await asyncio.gather(*tasks))
            return response

        # Aggregate results and exceptions, then filter them out
        # Use `None` upon exception for graceful error handling at GraphQL engine level
        #
        # NOTE: asyncio.gather(return_exceptions=True) catches and includes exceptions in the results
        #       this will become useful when we support exception handling in AppSync resolver
        results = await asyncio.gather(*tasks, return_exceptions=True)
        response.extend(None if isinstance(ret, Exception) else ret for ret in results)

        return response

    def _call_batch_resolver(self, event: list[dict], data_model: type[AppSyncResolverEvent]) -> list[Any]:
        """Call batch event resolver for sync and async methods

        Parameters
        ----------
        event : list[dict]
            Batch event
        data_model : type[AppSyncResolverEvent]
            Data_model to decode AppSync event, by default AppSyncResolverEvent or a subclass

        Returns
        -------
        list[Any]
            Results of the resolver execution.

        Raises
        ------
        InconsistentPayloadError:
            When all events in the batch do not have the same fieldName.

        ResolverNotFoundError:
            When no resolver is found for the specified type and field.
        """
        logger.debug("Processing batch resolver event")

        self.current_batch_event = [data_model(e) for e in event]
        type_name, field_name = self.current_batch_event[0].type_name, self.current_batch_event[0].field_name

        resolver = self._batch_resolver_registry.find_resolver(type_name, field_name)
        async_resolver = self._async_batch_resolver_registry.find_resolver(type_name, field_name)

        if resolver and async_resolver:
            warnings.warn(
                f"Both synchronous and asynchronous resolvers found for the same event and field."
                f"The synchronous resolver takes precedence. Executing: {resolver['func'].__name__}",
                stacklevel=2,
                category=PowertoolsUserWarning,
            )

        if resolver:
            logger.debug(f"Found sync resolver. {resolver=}, {field_name=}")
            return self._call_sync_batch_resolver(
                resolver=resolver["func"],
                raise_on_error=resolver["raise_on_error"],
                aggregate=resolver["aggregate"],
            )

        if async_resolver:
            logger.debug(f"Found async resolver. {resolver=}, {field_name=}")
            return asyncio.run(
                self._call_async_batch_resolver(
                    resolver=async_resolver["func"],
                    raise_on_error=async_resolver["raise_on_error"],
                    aggregate=async_resolver["aggregate"],
                ),
            )

        raise ResolverNotFoundError(f"No resolver found for '{type_name}.{field_name}'")

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
        self._resolver_registry.merge(router._resolver_registry)
        self._batch_resolver_registry.merge(router._batch_resolver_registry)
        self._async_batch_resolver_registry.merge(router._async_batch_resolver_registry)

    def resolver(self, type_name: str = "*", field_name: str | None = None) -> Callable:
        """Registers direct resolver function for GraphQL type and field name.

        Parameters
        ----------
        type_name : str, optional
            GraphQL type e.g., Query, Mutation, by default "*" meaning any
        field_name : Optional[str], optional
            GraphQL field e.g., getTodo, createTodo, by default None

        Returns
        -------
        Callable
            Registered resolver

        Example
        -------

        ```python
        from aws_lambda_powertools.event_handler import AppSyncResolver

        from typing import TypedDict

        app = AppSyncResolver()

        class Todo(TypedDict, total=False):
            id: str
            userId: str
            title: str
            completed: bool

        # resolve any GraphQL `getTodo` queries
        # arguments are injected as function arguments as-is
        @app.resolver(type_name="Query", field_name="getTodo")
        def get_todo(id: str = "", status: str = "open") -> Todo:
            todos: Response = requests.get(f"https://jsonplaceholder.typicode.com/todos/{id}")
            todos.raise_for_status()

            return todos.json()

        def lambda_handler(event, context):
            return app.resolve(event, context)
        ```
        """
        return self._resolver_registry.register(field_name=field_name, type_name=type_name)

    def batch_resolver(
        self,
        type_name: str = "*",
        field_name: str | None = None,
        raise_on_error: bool = False,
        aggregate: bool = True,
    ) -> Callable:
        """Registers batch resolver function for GraphQL type and field name.

        By default, we handle errors gracefully by returning `None`. If you want
        to short-circuit and fail the entire batch use `raise_on_error=True`.

        Parameters
        ----------
        type_name : str, optional
            GraphQL type e.g., Query, Mutation, by default "*" meaning any
        field_name : Optional[str], optional
            GraphQL field e.g., getTodo, createTodo, by default None
        raise_on_error : bool, optional
            Whether to fail entire batch upon error, or handle errors gracefully (None), by default False
        aggregate: bool
            A flag indicating whether the batch items should be processed at once or individually.
            If True (default), the batch resolver will process all items in the batch as a single event.
            If False, the batch resolver will process each item in the batch individually.

        Returns
        -------
        Callable
            Registered resolver
        """
        return self._batch_resolver_registry.register(
            field_name=field_name,
            type_name=type_name,
            raise_on_error=raise_on_error,
            aggregate=aggregate,
        )

    def async_batch_resolver(
        self,
        type_name: str = "*",
        field_name: str | None = None,
        raise_on_error: bool = False,
        aggregate: bool = True,
    ) -> Callable:
        return self._async_batch_resolver_registry.register(
            field_name=field_name,
            type_name=type_name,
            raise_on_error=raise_on_error,
            aggregate=aggregate,
        )

    def exception_handler(self, exc_class: type[Exception] | list[type[Exception]]):
        """
        A decorator function that registers a handler for one or more exception types.

        Parameters
        ----------
        exc_class (type[Exception] | list[type[Exception]])
            A single exception type or a list of exception types.

        Returns
        -------
        Callable:
            A decorator function that registers the exception handler.
        """

        return self.exception_handler_manager.exception_handler(exc_class=exc_class)
