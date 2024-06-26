from typing import Callable, Optional

from aws_lambda_powertools.event_handler.graphql_appsync._registry import ResolverRegistry
from aws_lambda_powertools.event_handler.graphql_appsync.base import BaseRouter


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
        aggregate: bool = True,
    ) -> Callable:
        return self._batch_resolver_registry.register(
            field_name=field_name,
            type_name=type_name,
            raise_on_error=raise_on_error,
            aggregate=aggregate,
        )

    def async_batch_resolver(
        self,
        type_name: str = "*",
        field_name: Optional[str] = None,
        raise_on_error: bool = False,
        aggregate: bool = True,
    ) -> Callable:
        return self._async_batch_resolver_registry.register(
            field_name=field_name,
            type_name=type_name,
            raise_on_error=raise_on_error,
            aggregate=aggregate,
        )

    def append_context(self, **additional_context):
        """Append key=value data as routing context"""
        self.context.update(**additional_context)

    def clear_context(self):
        """Resets routing context"""
        self.context.clear()
