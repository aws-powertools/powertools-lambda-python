from __future__ import annotations

import logging
import warnings
from typing import Any, Callable, Literal

from aws_lambda_powertools.event_handler.events_appsync.functions import find_best_route, is_valid_path
from aws_lambda_powertools.warnings import PowertoolsUserWarning

logger = logging.getLogger(__name__)

KIND_EVENT = Literal["on_publish", "async_on_publish", "on_subscribe"]

class ResolverEventsRegistry:
    def __init__(self, kind_resolver: str):
        self.resolvers: dict[str, dict[str, Any]] = {}
        self.kind_resolver = kind_resolver

    def register(
        self,
        path: str = "/default/*",
        aggregate: bool = False,
    ) -> Callable:
        """Registers the resolver for path that includes namespace + channel

        Parameters
        ----------
        path : str
            Path including namespace + channel
        aggregate: bool
            A flag indicating whether the batch items should be processed at once or individually.
            If True, the resolver will process all items as a single event.
            If False (default), the resolver will process each item individually.

        Return
        ----------
        Callable
            A Callable
        """
        if not is_valid_path(path):
            warnings.warn(
                f"The path `{path}` registered for `{self.kind_resolver}` is not valid and will be skipped."
                f"A path should always have a namespace starting with '/'"
                "A path can have multiple namespaces, all separated by '/'." 
                "Wildcards are allowed only at the end of the path.",
                stacklevel=2,
                category=PowertoolsUserWarning,
            )


        def _register(func) -> Callable:
            print(f"Adding resolver `{func.__name__}` for path `{path}` and kind_resolver `{self.kind_resolver}`")
            self.resolvers[f"{path}"] = {
                "func": func,
                "aggregate": aggregate,
            }
            return func

        return _register

    def find_resolver(self, path: str) -> dict | None:
        """Find resolver based on type_name and field_name

        Parameters
        ----------
        path : str
            Type name
        Return
        ----------
        dict | None
            A dictionary with the resolver and if this is aggregated or not
        """
        logger.debug(f"Looking for resolver for path `{path}` and kind_resolver `{self.kind_resolver}`")
        return self.resolvers.get(find_best_route(self.resolvers, path))

    def merge(self, other_registry: ResolverEventsRegistry):
        """Update current registry with incoming registry

        Parameters
        ----------
        other_registry : ResolverRegistry
            Registry to merge from
        """
        self.resolvers.update(**other_registry.resolvers)
