import logging
from typing import Any, Callable, Dict, Optional

from aws_lambda_powertools.event_handler.graphql_appsync.base import BaseResolverRegistry, BaseRouter

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


class ResolverRegistry(BaseResolverRegistry):
    def __init__(self):
        self._resolvers: Dict[str, Dict[str, Any]] = {}

    @property
    def resolvers(self) -> Dict[str, Dict[str, Any]]:
        return self._resolvers

    @resolvers.setter
    def resolvers(self, resolvers: dict) -> None:
        self._resolvers.update(resolvers)

    def resolver(self, type_name: str = "*", field_name: Optional[str] = None, raise_on_error: bool = False):
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

        def register(func):
            logger.debug(f"Adding resolver `{func.__name__}` for field `{type_name}.{field_name}`")
            self._resolvers[f"{type_name}.{field_name}"] = {"func": func, "raise_on_error": raise_on_error}
            return func

        return register

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

        resolver = self._resolvers.get(f"{type_name}.{field_name}", self._resolvers.get(f"*.{field_name}"))
        if not resolver:
            return None
        return resolver


class Router(BaseRouter):
    def __init__(self):
        self._resolver_registry: BaseResolverRegistry = ResolverRegistry()
        self._batch_resolver_registry: BaseResolverRegistry = ResolverRegistry()
        self._batch_async_resolver_registry: BaseResolverRegistry = ResolverRegistry()
        self._router_context: RouterContext = RouterContext()

    # Interfaces
    def resolver(self, type_name: str = "*", field_name: Optional[str] = None) -> Callable:
        return self._resolver_registry.resolver(field_name=field_name, type_name=type_name)

    def batch_resolver(
        self,
        type_name: str = "*",
        field_name: Optional[str] = None,
        raise_on_error: bool = False,
    ) -> Callable:
        return self._batch_resolver_registry.resolver(
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
        return self._batch_async_resolver_registry.resolver(
            field_name=field_name,
            type_name=type_name,
            raise_on_error=raise_on_error,
        )

    def append_context(self, **additional_context) -> None:
        self._router_context.context = additional_context
