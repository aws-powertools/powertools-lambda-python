import logging
from typing import Any, Callable, Dict, Optional

from aws_lambda_powertools.event_handler.graphql_appsync.base import BaseRouter

logger = logging.getLogger(__name__)


class ResolverRegistry:
    def __init__(self):
        self.resolvers: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        type_name: str = "*",
        field_name: Optional[str] = None,
        raise_on_error: bool = False,
    ) -> Callable:
        """Registers the resolver for field_name

        Parameters
        ----------
        type_name : str
            Type name
        field_name : str
            Field name
        raise_on_error: bool
            A flag indicating whether to raise an error when processing batches
            with failed items. Defaults to False, which means errors are handled without raising exceptions.

        Return
        ----------
        Dict
            A dictionary with the resolver and if raise exception on error
        """

        def _register(func) -> Callable:
            logger.debug(f"Adding resolver `{func.__name__}` for field `{type_name}.{field_name}`")
            self.resolvers[f"{type_name}.{field_name}"] = {"func": func, "raise_on_error": raise_on_error}
            return func

        return _register

    def find_resolver(self, type_name: str, field_name: str) -> Optional[Dict]:
        """Find resolver based on type_name and field_name

        Parameters
        ----------
        type_name : str
            Type name
        field_name : str
            Field name
        Return
        ----------
        Optional[Dict]
            A dictionary with the resolver and if raise exception on error
        """

        return self.resolvers.get(f"{type_name}.{field_name}", self.resolvers.get(f"*.{field_name}"))

    def merge(self, other_registry: "ResolverRegistry"):
        """Update current registry with incoming registry

        Parameters
        ----------
        other_registry : ResolverRegistry
            Registry to merge from
        """
        self.resolvers.update(**other_registry.resolvers)


class Router(BaseRouter):
    context: dict

    def __init__(self):
        self.context = {}  # early init as customers might add context before event resolution
        self._resolver_registry = ResolverRegistry()
        self._batch_resolver_registry = ResolverRegistry()
        self._async_batch_resolver_registry = ResolverRegistry()

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

    def append_context(self, **additional_context):
        """Append key=value data as routing context"""
        self.context.update(**additional_context)

    def clear_context(self):
        """Resets routing context"""
        self.context.clear()
