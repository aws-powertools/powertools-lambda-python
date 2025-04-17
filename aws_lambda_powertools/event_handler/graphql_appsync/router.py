from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.event_handler.graphql_appsync._registry import ResolverRegistry
from aws_lambda_powertools.event_handler.graphql_appsync.base import BaseRouter

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.utilities.data_classes.appsync_resolver_event import AppSyncResolverEvent
    from aws_lambda_powertools.utilities.typing.lambda_context import LambdaContext


class Router(BaseRouter):
    context: dict
    current_batch_event: list[AppSyncResolverEvent] = []
    current_event: AppSyncResolverEvent | None = None
    lambda_context: LambdaContext | None = None

    def __init__(self):
        self.context = {}  # early init as customers might add context before event resolution
        self._resolver_registry = ResolverRegistry()
        self._batch_resolver_registry = ResolverRegistry()
        self._async_batch_resolver_registry = ResolverRegistry()

    def resolver(self, type_name: str = "*", field_name: str | None = None) -> Callable:
        return self._resolver_registry.register(field_name=field_name, type_name=type_name)

    def batch_resolver(
        self,
        type_name: str = "*",
        field_name: str | None = None,
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

    def append_context(self, **additional_context):
        """Append key=value data as routing context"""
        self.context.update(**additional_context)

    def clear_context(self):
        """Resets routing context"""
        self.context.clear()
