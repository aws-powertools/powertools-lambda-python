import asyncio
import logging
import warnings
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, Union

from aws_lambda_powertools.event_handler.exceptions_appsync import InconsistentPayload, ResolverNotFound
from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = logging.getLogger(__name__)


class RouterContext:
    def __init__(self):
        self._context = {}

    @property
    def context(self) -> Dict[str, Any]:
        return self._context

    @context.setter
    def context(self, additional_context: Dict[str, Any]) -> None:
        """Append key=value data as routing context"""
        self._context.update(**additional_context)

    @context.deleter
    def context(self):
        """Resets routing context"""
        self._context.clear()


class BaseResolverRegistry(ABC):
    """
    Abstract base class for a resolver registry.

    This class defines the interface for managing and retrieving resolvers
    for various type and field combinations.
    """

    @property
    @abstractmethod
    def resolvers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the dictionary of resolvers.

        Returns
        -------
        dict
            A dictionary containing resolver information.
        """
        raise NotImplementedError

    @resolvers.setter
    @abstractmethod
    def resolvers(self, resolvers: dict) -> None:
        """
        Set the dictionary of resolvers.

        Parameters
        ----------
        resolvers: dict
            A dictionary containing resolver information.
        """
        raise NotImplementedError

    @abstractmethod
    def resolver(self, type_name: str = "*", field_name: Optional[str] = None) -> Callable:
        """
        Retrieve a resolver function for a specific type and field.

        Parameters
        -----------
        type_name: str
            The name of the type.
        field_name: Optional[str]
            The name of the field (default is None).

        Returns
        -------
        Callable
            The resolver function.
        """
        raise NotImplementedError

    @abstractmethod
    def find_resolver(self, type_name: str, field_name: str) -> Optional[Callable]:
        """
        Find a resolver function for a specific type and field.

        Parameters
        -----------
        type_name: str
            The name of the type.
        field_name: str
            The name of the field.

        Returns
        -------
        Optional[Callable]
            The resolver function. None if not found.
        """
        raise NotImplementedError


class BasePublic(ABC):
    """
    Abstract base class for public interface methods for resolver.

    This class outlines the methods that must be implemented by subclasses to manage resolvers and
    context information.
    """

    @abstractmethod
    def resolver(self, type_name: str = "*", field_name: Optional[str] = None) -> Callable:
        """
        Retrieve a resolver function for a specific type and field.

        Parameters
        -----------
        type_name: str
            The name of the type.
        field_name: Optional[str]
            The name of the field (default is None).

        Examples
        --------
        ```python
        from typing import Optional

        from aws_lambda_powertools.event_handler import AppSyncResolver
        from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
        from aws_lambda_powertools.utilities.typing import LambdaContext

        app = AppSyncResolver()

        @app.resolver(type_name="Query", field_name="getPost")
        def related_posts(event: AppSyncResolverEvent) -> Optional[list]:
            return {"success": "ok"}

        def lambda_handler(event, context: LambdaContext) -> dict:
            return app.resolve(event, context)
        ```

        Returns
        -------
        Callable
            The resolver function.
        """
        raise NotImplementedError

    @abstractmethod
    def batch_resolver(self, type_name: str = "*", field_name: Optional[str] = None) -> Callable:
        """
        Retrieve a batch resolver function for a specific type and field.

        Parameters
        -----------
        type_name: str
            The name of the type.
        field_name: Optional[str]
            The name of the field (default is None).

        Examples
        --------
        ```python
        from typing import Optional

        from aws_lambda_powertools.event_handler import AppSyncResolver
        from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
        from aws_lambda_powertools.utilities.typing import LambdaContext

        app = AppSyncResolver()

        @app.batch_resolver(type_name="Query", field_name="getPost")
        def related_posts(event: AppSyncResolverEvent, id) -> Optional[list]:
            return {"post_id": id}

        def lambda_handler(event, context: LambdaContext) -> dict:
            return app.resolve(event, context)
        ```

        Returns
        -------
        Callable
            The batch resolver function.
        """
        raise NotImplementedError

    @abstractmethod
    def batch_async_resolver(self, type_name: str = "*", field_name: Optional[str] = None) -> Callable:
        """
        Retrieve a batch resolver function for a specific type and field.

        Parameters
        -----------
        type_name: str
            The name of the type.
        field_name: Optional[str]
            The name of the field (default is None).

        Examples
        --------
        ```python
        from typing import Optional

        from aws_lambda_powertools.event_handler import AppSyncResolver
        from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
        from aws_lambda_powertools.utilities.typing import LambdaContext

        app = AppSyncResolver()

        @app.batch_async_resolver(type_name="Query", field_name="getPost")
        async def related_posts(event: AppSyncResolverEvent, id) -> Optional[list]:
            return {"post_id": id}

        def lambda_handler(event, context: LambdaContext) -> dict:
            return app.resolve(event, context)
        ```

        Returns
        -------
        Callable
            The batch resolver function.
        """
        raise NotImplementedError

    @abstractmethod
    def append_context(self, **additional_context) -> None:
        """
        Append additional context information.

        Parameters
        -----------
        **additional_context: dict
            Additional context key-value pairs to append.
        """
        raise NotImplementedError


class ResolverRegistry(BaseResolverRegistry):
    def __init__(self):
        self._resolvers: Dict[str, Dict[str, Any]] = {}

    @property
    def resolvers(self) -> Dict[str, Dict[str, Any]]:
        return self._resolvers

    @resolvers.setter
    def resolvers(self, resolvers: dict) -> None:
        self._resolvers.update(resolvers)

    def resolver(self, type_name: str = "*", field_name: Optional[str] = None):
        """Registers the resolver for field_name

        Parameters
        ----------
        type_name : str
            Type name
        field_name : str
            Field name
        """

        def register(func):
            logger.debug(f"Adding resolver `{func.__name__}` for field `{type_name}.{field_name}`")
            self._resolvers[f"{type_name}.{field_name}"] = {"func": func}
            return func

        return register

    def find_resolver(self, type_name: str, field_name: str) -> Optional[Callable]:
        """Find resolver based on type_name and field_name

        Parameters
        ----------
        type_name : str
            Type name
        field_name : str
            Field name
        """

        resolver = self._resolvers.get(f"{type_name}.{field_name}", self._resolvers.get(f"*.{field_name}"))
        if not resolver:
            return None
        return resolver["func"]


class Router(BasePublic):
    def __init__(self):
        self._resolver_registry: BaseResolverRegistry = ResolverRegistry()
        self._batch_resolver_registry: BaseResolverRegistry = ResolverRegistry()
        self._batch_async_resolver_registry: BaseResolverRegistry = ResolverRegistry()
        self._router_context: RouterContext = RouterContext()

    # Interfaces
    def resolver(self, type_name: str = "*", field_name: Optional[str] = None) -> Callable:
        return self._resolver_registry.resolver(field_name=field_name, type_name=type_name)

    def batch_resolver(self, type_name: str = "*", field_name: Optional[str] = None) -> Callable:
        return self._batch_resolver_registry.resolver(field_name=field_name, type_name=type_name)

    def batch_async_resolver(self, type_name: str = "*", field_name: Optional[str] = None) -> Callable:
        return self._batch_async_resolver_registry.resolver(field_name=field_name, type_name=type_name)

    def append_context(self, **additional_context) -> None:
        self._router_context.context = additional_context


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

    def __init__(self, raise_error_on_failed_batch: bool = False):
        """
        Initialize a new instance of the AppSyncResolver.

        Parameters
        ----------
        raise_error_on_failed_batch: bool
            A flag indicating whether to raise an error when processing batches
            with failed items. Defaults to False, which means errors are handled without raising exceptions.
        """
        super().__init__()
        self.current_batch_event: List[AppSyncResolverEvent] = []
        self.current_event: Optional[AppSyncResolverEvent] = None
        self.lambda_context: Optional[LambdaContext] = None
        self.raise_error_on_failed_batch = raise_error_on_failed_batch

    def resolve(
        self,
        event: Union[dict, List[Dict]],
        context: LambdaContext,
        data_model: Type[AppSyncResolverEvent] = AppSyncResolverEvent,
    ) -> Any:
        """Resolve field_name in single event or in a batch event

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

        response = (
            self._call_batch_resolver(event=event, data_model=data_model)
            if isinstance(event, list)
            else self._call_single_resolver(event=event, data_model=data_model)
        )
        del self._router_context.context

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
        return resolver(**self.current_event.arguments)

    def _call_sync_batch_resolver(self, sync_resolver: Callable) -> List[Any]:
        """
        Calls a synchronous batch resolver function for each event in the current batch.

        Parameters
        ----------
        sync_resolver: Callable
            The callable function to resolve events.

        Returns
        -------
        List[Any]
            A list of results corresponding to the resolved events.
        """
        results: List = []

        # Check if we should raise errors or continue and append None in failed records
        if not self.raise_error_on_failed_batch:
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

    async def _async_process_batch_event(
        self,
        async_resolver: Callable,
        appconfig_event: AppSyncResolverEvent,
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
        **kwargs
            Additional keyword arguments to pass to the resolver.

        Returns
        -------
        Any
            The result of the resolver function or None if an error occurs and self.raise_error_on_failed_batch is False
        """

        if not self.raise_error_on_failed_batch:
            try:
                return await async_resolver(event=appconfig_event, **kwargs)
            except Exception:
                return None

        # If raise_error_on_failed_batch is False, proceed without raising errors
        return await async_resolver(event=appconfig_event, **kwargs)

    async def _call_async_batch_resolver(self, async_resolver: Callable) -> List[Any]:
        """
        Asynchronously call a batch resolver for each event in the current batch.

        Parameters
        ----------
        async_resolver: Callable
            The asynchronous resolver function.

        Returns
        -------
        List[Any]
            A list of results corresponding to the resolved events.
        """
        return list(
            await asyncio.gather(
                *[
                    self._async_process_batch_event(async_resolver, appconfig_event, **appconfig_event.arguments)
                    for appconfig_event in self.current_batch_event
                ],
            ),
        )

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
        async_resolver = self._batch_async_resolver_registry.find_resolver(type_name, field_name)

        if resolver and async_resolver:
            warnings.warn(
                f"Both synchronous and asynchronous resolvers found for the same event and field."
                f"The synchronous resolver takes precedence. Executing: {resolver.__name__}",
                stacklevel=2,
            )

        if resolver:
            return self._call_sync_batch_resolver(resolver)
        elif async_resolver:
            return asyncio.run(self._call_async_batch_resolver(async_resolver))
        else:
            raise ResolverNotFound(f"No resolver found for '{type_name}.{field_name}'")

    def __call__(
        self,
        event: dict,
        context: LambdaContext,
        data_model: Type[AppSyncResolverEvent] = AppSyncResolverEvent,
    ) -> Any:
        """Implicit lambda handler which internally calls `resolve`"""
        return self.resolve(event, context, data_model)

    def include_router(self, router: "Router") -> None:
        """Adds all resolvers defined in a router

        Parameters
        ----------
        router : Router
            A router containing a dict of field resolvers
        """

        # Merge app and router context
        self._router_context.context = router._router_context.context
        # use pointer to allow context clearance after event is processed e.g., resolve(evt, ctx)
        router._router_context._context = self._router_context.context

        self._resolver_registry.resolvers = router._resolver_registry.resolvers
        self._batch_resolver_registry.resolvers = router._batch_resolver_registry.resolvers
        self._batch_async_resolver_registry.resolvers = router._batch_async_resolver_registry.resolvers

    # Interfaces
    def resolver(self, type_name: str = "*", field_name: Optional[str] = None) -> Callable:
        return self._resolver_registry.resolver(field_name=field_name, type_name=type_name)

    def batch_resolver(self, type_name: str = "*", field_name: Optional[str] = None) -> Callable:
        return self._batch_resolver_registry.resolver(field_name=field_name, type_name=type_name)

    def batch_async_resolver(self, type_name: str = "*", field_name: Optional[str] = None) -> Callable:
        return self._batch_async_resolver_registry.resolver(field_name=field_name, type_name=type_name)

    def append_context(self, **additional_context) -> None:
        self._router_context.context = additional_context
