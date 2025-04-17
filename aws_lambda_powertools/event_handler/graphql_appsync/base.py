from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class BaseRouter(ABC):
    """Abstract base class for Router (resolvers)"""

    @abstractmethod
    def resolver(self, type_name: str = "*", field_name: str | None = None) -> Callable:
        """
        Retrieve a resolver function for a specific type and field.

        Parameters
        -----------
        type_name: str
            The name of the type.
        field_name: str, optional
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
    def batch_resolver(
        self,
        type_name: str = "*",
        field_name: str | None = None,
        raise_on_error: bool = False,
        aggregate: bool = True,
    ) -> Callable:
        """
        Retrieve a batch resolver function for a specific type and field.

        Parameters
        -----------
        type_name: str
            The name of the type.
        field_name: str, optional
            The name of the field (default is None).
        raise_on_error: bool
            A flag indicating whether to raise an error when processing batches
            with failed items. Defaults to False, which means errors are handled without raising exceptions.
        aggregate: bool
            A flag indicating whether the batch items should be processed at once or individually.
            If True (default), the batch resolver will process all items in the batch as a single event.
            If False, the batch resolver will process each item in the batch individually.

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
    def async_batch_resolver(
        self,
        type_name: str = "*",
        field_name: str | None = None,
        raise_on_error: bool = False,
        aggregate: bool = True,
    ) -> Callable:
        """
        Retrieve a batch resolver function for a specific type and field and runs async.

        Parameters
        -----------
        type_name: str
            The name of the type.
        field_name: str, optional
            The name of the field (default is None).
        raise_on_error: bool
            A flag indicating whether to raise an error when processing batches
            with failed items. Defaults to False, which means errors are handled without raising exceptions.
        aggregate: bool
            A flag indicating whether the batch items should be processed at once or individually.
            If True (default), the batch resolver will process all items in the batch as a single event.
            If False, the batch resolver will process each item in the batch individually.

        Examples
        --------
        ```python
        from typing import Optional

        from aws_lambda_powertools.event_handler import AppSyncResolver
        from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
        from aws_lambda_powertools.utilities.typing import LambdaContext

        app = AppSyncResolver()

        @app.async_batch_resolver(type_name="Query", field_name="getPost")
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
        Appends context information available under any route.

        Parameters
        -----------
        **additional_context: dict
            Additional context key-value pairs to append.
        """
        raise NotImplementedError
