import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ResolverRegistry:
    def __init__(self):
        self.resolvers: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        type_name: str = "*",
        field_name: Optional[str] = None,
        raise_on_error: bool = False,
        aggregate: bool = True,
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
        aggregate: bool
            A flag indicating whether the batch items should be processed at once or individually.
            If True (default), the batch resolver will process all items in the batch as a single event.
            If False, the batch resolver will process each item in the batch individually.

        Return
        ----------
        Dict
            A dictionary with the resolver and if raise exception on error
        """

        def _register(func) -> Callable:
            logger.debug(f"Adding resolver `{func.__name__}` for field `{type_name}.{field_name}`")
            self.resolvers[f"{type_name}.{field_name}"] = {
                "func": func,
                "raise_on_error": raise_on_error,
                "aggregate": aggregate,
            }
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
        logger.debug(f"Looking for resolver for type={type_name}, field={field_name}.")
        return self.resolvers.get(f"{type_name}.{field_name}", self.resolvers.get(f"*.{field_name}"))

    def merge(self, other_registry: "ResolverRegistry"):
        """Update current registry with incoming registry

        Parameters
        ----------
        other_registry : ResolverRegistry
            Registry to merge from
        """
        self.resolvers.update(**other_registry.resolvers)
