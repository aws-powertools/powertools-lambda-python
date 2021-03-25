from typing import Any, Dict

from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.typing import LambdaContext


class AppSyncResolver:
    """
    AppSync resolver decorator

    Example
    -------

    **Sample usage**

        from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
        from aws_lambda_powertools.utilities.event_handler import AppSyncResolver

        app = AppSyncResolver()

        @app.resolver(type_name="Query", field_name="listLocations", include_event=True)
        def list_locations(event: AppSyncResolverEvent, page: int = 0, size: int = 10):
            # Your logic to fetch locations
            ...

        @app.resolver(type_name="Merchant", field_name="extraInfo", include_event=True)
        def get_extra_info(event: AppSyncResolverEvent):
            # Can use "event.source" to filter within the parent context
            ...

        @app.resolver(field_name="commonField")
        def common_field():
            # Would match all fieldNames matching 'commonField'
            ...

        def handle(event, context):
            app.resolve(event, context)

    """

    def __init__(self):
        self._resolvers: dict = {}

    def resolver(
        self,
        type_name: str = "*",
        field_name: str = None,
        include_event: bool = False,
        include_context: bool = False,
        **kwargs,
    ):
        """Registers the resolver for field_name

        Parameters
        ----------
        type_name : str
            Type name
        field_name : str
            Field name
        include_event: bool
            Whether to include the lambda event
        include_context: bool
            Whether to include the lambda context
        kwargs :
            Extra options via kwargs
        """

        def register_resolver(func):
            kwargs["include_event"] = include_event
            kwargs["include_context"] = include_context
            self._resolvers[f"{type_name}.{field_name}"] = {
                "func": func,
                "config": kwargs,
            }
            return func

        return register_resolver

    def resolve(self, _event: dict, context: LambdaContext) -> Any:
        """Resolve field_name

        Parameters
        ----------
        _event : dict
            Lambda event
        context : LambdaContext
            Lambda context

        Returns
        -------
        Any
            Returns the result of the resolver

        Raises
        -------
        ValueError
            If we could not find a field resolver
        """
        event = AppSyncResolverEvent(_event)
        resolver, config = self._resolver(event.type_name, event.field_name)
        kwargs = self._kwargs(event, context, config)
        return resolver(**kwargs)

    def _resolver(self, type_name: str, field_name: str) -> tuple:
        """Find resolver for field_name

        Parameters
        ----------
        type_name : str
            Type name
        field_name : str
            Field name

        Returns
        -------
        tuple
            callable function and configuration
        """
        full_name = f"{type_name}.{field_name}"
        resolver = self._resolvers.get(full_name, self._resolvers.get(f"*.{field_name}"))
        if not resolver:
            raise ValueError(f"No resolver found for '{full_name}'")
        return resolver["func"], resolver["config"]

    @staticmethod
    def _kwargs(event: AppSyncResolverEvent, context: LambdaContext, config: dict) -> Dict[str, Any]:
        """Get the keyword arguments
        Parameters
        ----------
        event : AppSyncResolverEvent
            Lambda event
        context : LambdaContext
            Lambda context
        config : dict
            Configuration settings
        Returns
        -------
        dict
            Returns keyword arguments
        """
        kwargs = {**event.arguments}
        if config.get("include_event", False):
            kwargs["event"] = event
        if config.get("include_context", False):
            kwargs["context"] = context
        return kwargs
