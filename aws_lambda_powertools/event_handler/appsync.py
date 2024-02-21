import asyncio
import warnings
from typing import Any, Callable, Dict, List, Optional, Type, Union

from aws_lambda_powertools.event_handler.exceptions_appsync import InconsistentPayload, ResolverNotFound
from aws_lambda_powertools.event_handler.graphql_appsync.router import Router
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.typing import LambdaContext


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

        self.current_batch_event: List[AppSyncResolverEvent] = []
        self.current_event: Optional[AppSyncResolverEvent] = None
        self.lambda_context: Optional[LambdaContext] = None

    def __call__(
        self,
        event: dict,
        context: LambdaContext,
        data_model: Type[AppSyncResolverEvent] = AppSyncResolverEvent,
    ) -> Any:
        """Implicit lambda handler which internally calls `resolve`"""
        return self.resolve(event, context, data_model)

    def resolve(
        self,
        event: Union[dict, List[Dict]],
        context: LambdaContext,
        data_model: Type[AppSyncResolverEvent] = AppSyncResolverEvent,
    ) -> Any:
        """Resolves the response based on the provide event and decorator routes

        Parameters
        ----------
        event : dict | List[Dict]
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
                return self.request_headers.get("cloudfront-viewer-country")


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

        if isinstance(event, list):
            response = self._call_batch_resolver(event=event, data_model=data_model)
        else:
            response = self._call_single_resolver(event=event, data_model=data_model)

        self.clear_context()

        return response

    def _call_single_resolver(self, event: dict, data_model: Type[AppSyncResolverEvent]) -> Any:
        """Call single event resolver

        Parameters
        ----------
        event : dict
            Event
        data_model : Type[AppSyncResolverEvent]
            Data_model to decode AppSync event, by default it is of AppSyncResolverEvent type or subclass of it
        """

        self.current_event = data_model(event)
        resolver = self._resolver_registry.find_resolver(self.current_event.type_name, self.current_event.field_name)
        if not resolver:
            raise ValueError(f"No resolver found for '{self.current_event.type_name}.{self.current_event.field_name}'")
        return resolver["func"](**self.current_event.arguments)

    def _call_sync_batch_resolver(self, sync_resolver: Callable, raise_on_error: bool = False) -> List[Any]:
        """
        Calls a synchronous batch resolver function for each event in the current batch.

        Parameters
        ----------
        sync_resolver: Callable
            The callable function to resolve events.
        raise_on_error: bool
            A flag indicating whether to raise an error when processing batches
            with failed items. Defaults to False, which means errors are handled without raising exceptions.

        Returns
        -------
        List[Any]
            A list of results corresponding to the resolved events.
        """

        # Check if we should raise errors or continue and append None in failed records
        if not raise_on_error:
            results: List = []
            for appconfig_event in self.current_batch_event:
                try:
                    results.append(sync_resolver(event=appconfig_event, **appconfig_event.arguments))
                except Exception:
                    # If an error occurs and raise_error_on_failed_batch is False,
                    # append None to the results and continue with the next event.
                    results.append(None)

            return results

        return [
            sync_resolver(event=appconfig_event, **appconfig_event.arguments)
            for appconfig_event in self.current_batch_event
        ]

    async def _call_async_batch_resolver(self, async_resolver: Callable, raise_on_error: bool = False) -> List[Any]:
        """
        Asynchronously call a batch resolver for each event in the current batch.

        Parameters
        ----------
        async_resolver: Callable
            The asynchronous resolver function.
        raise_on_error: bool
            A flag indicating whether to raise an error when processing batches
            with failed items. Defaults to False, which means errors are handled without raising exceptions.

        Returns
        -------
        List[Any]
            A list of results corresponding to the resolved events.
        """
        return list(
            await asyncio.gather(
                *[
                    self._async_process_batch_event(
                        async_resolver,
                        appconfig_event,
                        **appconfig_event.arguments,
                        raise_on_error=raise_on_error,
                    )
                    for appconfig_event in self.current_batch_event
                ],
            ),
        )

    async def _async_process_batch_event(
        self,
        async_resolver: Callable,
        appconfig_event: AppSyncResolverEvent,
        raise_on_error: bool = False,
        **kwargs,
    ):
        """
        Asynchronously process a batch event using the provided async_resolver.

        Parameters
        ----------
        async_resolver: Callable
            The asynchronous resolver function.
        appconfig_event: AppSyncResolverEvent
            The event to process.
        raise_on_error: bool
            A flag indicating whether to raise an error when processing batches
            with failed items. Defaults to False, which means errors are handled without raising exceptions.
        **kwargs
            Additional keyword arguments to pass to the resolver.

        Returns
        -------
        Any
            The result of the resolver function or None if an error occurs and self.raise_error_on_failed_batch is False
        """

        if not raise_on_error:
            try:
                return await async_resolver(event=appconfig_event, **kwargs)
            except Exception:
                return None

        # If raise_error_on_failed_batch is False, proceed without raising errors
        return await async_resolver(event=appconfig_event, **kwargs)

    def _call_batch_resolver(self, event: List[dict], data_model: Type[AppSyncResolverEvent]) -> List[Any]:
        """Call batch event resolver for sync and async methods

        Parameters
        ----------
        event : List[dict]
            Event
        data_model : Type[AppSyncResolverEvent]
            Data_model to decode AppSync event, by default it is of AppSyncResolverEvent type or subclass of it

        Returns
        -------
        List[Any]
            Results of the resolver execution.

        Raises
        ------
        InconsistentPayload:
            If all events in the batch do not have the same fieldName.

        ResolverNotFound:
            If no resolver is found for the specified type and field.
        """

        # All events in the batch must have the same fieldName
        field_names = {field_name["info"]["fieldName"] for field_name in event}
        if len(field_names) > 1:
            raise InconsistentPayload(f"All events in the batch must have the same fieldName. Found: {field_names}")

        self.current_batch_event = [data_model(e) for e in event]
        type_name, field_name = self.current_batch_event[0].type_name, self.current_batch_event[0].field_name

        resolver = self._batch_resolver_registry.find_resolver(type_name, field_name)
        async_resolver = self._async_batch_resolver_registry.find_resolver(type_name, field_name)

        if resolver and async_resolver:
            warnings.warn(
                f"Both synchronous and asynchronous resolvers found for the same event and field."
                f"The synchronous resolver takes precedence. Executing: {resolver['func'].__name__}",
                stacklevel=2,
            )

        if resolver:
            return self._call_sync_batch_resolver(resolver["func"], resolver["raise_on_error"])
        elif async_resolver:
            return asyncio.run(
                self._call_async_batch_resolver(async_resolver["func"], async_resolver["raise_on_error"]),
            )
        else:
            raise ResolverNotFound(f"No resolver found for '{type_name}.{field_name}'")

    def include_router(self, router: "Router") -> None:
        """Adds all resolvers defined in a router

        Parameters
        ----------
        router : Router
            A router containing a dict of field resolvers
        """

        # Merge app and router context
        self.context.update(**router.context)

        # use pointer to allow context clearance after event is processed e.g., resolve(evt, ctx)
        router.context = self.context

        self._resolver_registry.merge(router._resolver_registry)
        self._batch_resolver_registry.merge(router._batch_resolver_registry)
        self._async_batch_resolver_registry.merge(router._async_batch_resolver_registry)

    def resolver(self, type_name: str = "*", field_name: Optional[str] = None) -> Callable:
        return self._resolver_registry.register(field_name=field_name, type_name=type_name)

    def batch_resolver(
        self,
        type_name: str = "*",
        field_name: Optional[str] = None,
        raise_on_error: bool = False,
    ) -> Callable:
        return self._batch_resolver_registry.register(
            field_name=field_name,
            type_name=type_name,
            raise_on_error=raise_on_error,
        )

    def async_batch_resolver(
        self,
        type_name: str = "*",
        field_name: Optional[str] = None,
        raise_on_error: bool = False,
    ) -> Callable:
        return self._async_batch_resolver_registry.register(
            field_name=field_name,
            type_name=type_name,
            raise_on_error=raise_on_error,
        )
