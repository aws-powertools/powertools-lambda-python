import logging
from typing import Any, Callable, Optional, Type, TypeVar

from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = logging.getLogger(__name__)

AppSyncResolverEventT = TypeVar("AppSyncResolverEventT", bound=AppSyncResolverEvent)


class AppSyncResolver:
    """
    AppSync resolver decorator

    Example
    -------

    **Sample usage**

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
    """

    current_event: AppSyncResolverEventT  # type: ignore[valid-type]
    lambda_context: LambdaContext

    def __init__(self):
        self._resolvers: dict = {}

    def resolver(self, type_name: str = "*", field_name: Optional[str] = None):
        """Registers the resolver for field_name

        Parameters
        ----------
        type_name : str
            Type name
        field_name : str
            Field name
        """

        def register_resolver(func):
            logger.debug(f"Adding resolver `{func.__name__}` for field `{type_name}.{field_name}`")
            self._resolvers[f"{type_name}.{field_name}"] = {"func": func}
            return func

        return register_resolver

    def resolve(
        self, event: dict, context: LambdaContext, data_model: Type[AppSyncResolverEvent] = AppSyncResolverEvent
    ) -> Any:
        """Resolve field_name

        Parameters
        ----------
        event : dict
            Lambda event
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
        self.current_event = data_model(event)
        self.lambda_context = context
        resolver = self._get_resolver(self.current_event.type_name, self.current_event.field_name)
        return resolver(**self.current_event.arguments)

    def _get_resolver(self, type_name: str, field_name: str) -> Callable:
        """Get resolver for field_name

        Parameters
        ----------
        type_name : str
            Type name
        field_name : str
            Field name

        Returns
        -------
        Callable
            callable function and configuration
        """
        full_name = f"{type_name}.{field_name}"
        resolver = self._resolvers.get(full_name, self._resolvers.get(f"*.{field_name}"))
        if not resolver:
            raise ValueError(f"No resolver found for '{full_name}'")
        return resolver["func"]

    def __call__(
        self, event: dict, context: LambdaContext, data_model: Type[AppSyncResolverEvent] = AppSyncResolverEvent
    ) -> Any:
        """Implicit lambda handler which internally calls `resolve`"""
        return self.resolve(event, context, data_model)
