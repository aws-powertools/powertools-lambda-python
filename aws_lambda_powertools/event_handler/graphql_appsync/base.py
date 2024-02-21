from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional


class BaseResolverRegistry(ABC):
    """
    Abstract base class for a resolver registry.

    This class defines the interface for managing and retrieving resolvers
    for various type and field combinations.
    """

    @property
    @abstractmethod
    def resolvers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the dictionary of resolvers.

        Returns
        -------
        dict
            A dictionary containing resolver information.
        """
        raise NotImplementedError

    @resolvers.setter
    @abstractmethod
    def resolvers(self, resolvers: dict) -> None:
        """
        Set the dictionary of resolvers.

        Parameters
        ----------
        resolvers: dict
            A dictionary containing resolver information.
        """
        raise NotImplementedError

    @abstractmethod
    def resolver(
        self,
        type_name: str = "*",
        field_name: Optional[str] = None,
        raise_on_error: bool = False,
    ):
        """
        Retrieve a resolver function for a specific type and field.

        Parameters
        -----------
        type_name: str
            The name of the type.
        field_name: Optional[str]
            The name of the field (default is None).
        raise_on_error: bool
            A flag indicating whether to raise an error when processing batches
            with failed items. Defaults to False, which means errors are handled without raising exceptions.

        Returns
        -------
        Callable
            The resolver function.
        """
        raise NotImplementedError

    @abstractmethod
    def find_resolver(self, type_name: str, field_name: str) -> Optional[Dict]:
        """
        Find a resolver function for a specific type and field.

        Parameters
        -----------
        type_name: str
            The name of the type.
        field_name: str
            The name of the field.

        Returns
        -------
        Optional[Callable]
            The resolver function. None if not found.
        """
        raise NotImplementedError


class BasePublic(ABC):
    """
    Abstract base class for public interface methods for resolver.

    This class outlines the methods that must be implemented by subclasses to manage resolvers and
    context information.
    """

    @abstractmethod
    def resolver(self, type_name: str = "*", field_name: Optional[str] = None) -> Callable:
        """
        Retrieve a resolver function for a specific type and field.

        Parameters
        -----------
        type_name: str
            The name of the type.
        field_name: Optional[str]
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
        field_name: Optional[str] = None,
        raise_on_error: bool = False,
    ) -> Callable:
        """
        Retrieve a batch resolver function for a specific type and field.

        Parameters
        -----------
        type_name: str
            The name of the type.
        field_name: Optional[str]
            The name of the field (default is None).
        raise_on_error: bool
            A flag indicating whether to raise an error when processing batches
            with failed items. Defaults to False, which means errors are handled without raising exceptions.

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
        field_name: Optional[str] = None,
        raise_on_error: bool = False,
    ) -> Callable:
        """
        Retrieve a batch resolver function for a specific type and field and runs async.

        Parameters
        -----------
        type_name: str
            The name of the type.
        field_name: Optional[str]
            The name of the field (default is None).
        raise_on_error: bool
            A flag indicating whether to raise an error when processing batches
            with failed items. Defaults to False, which means errors are handled without raising exceptions.

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
        Append additional context information.

        Parameters
        -----------
        **additional_context: dict
            Additional context key-value pairs to append.
        """
        raise NotImplementedError
