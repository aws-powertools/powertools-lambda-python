from typing import Any, Dict

from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.typing import LambdaContext


class AppSyncResolver:
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
        def register_resolver(func):
            kwargs["include_event"] = include_event
            kwargs["include_context"] = include_context
            self._resolvers[f"{type_name}.{field_name}"] = {
                "func": func,
                "config": kwargs,
            }
            return func

        return register_resolver

    def resolve(self, event: dict, context: LambdaContext) -> Any:
        event = AppSyncResolverEvent(event)
        resolver, config = self._resolver(event.type_name, event.field_name)
        kwargs = self._kwargs(event, context, config)
        return resolver(**kwargs)

    def _resolver(self, type_name: str, field_name: str) -> tuple:
        full_name = f"{type_name}.{field_name}"
        resolver = self._resolvers.get(full_name, self._resolvers.get(f"*.{field_name}"))
        if not resolver:
            raise ValueError(f"No resolver found for '{full_name}'")
        return resolver["func"], resolver["config"]

    @staticmethod
    def _kwargs(event: AppSyncResolverEvent, context: LambdaContext, config: dict) -> Dict[str, Any]:
        kwargs = {**event.arguments}
        if config.get("include_event", False):
            kwargs["event"] = event
        if config.get("include_context", False):
            kwargs["context"] = context
        return kwargs
