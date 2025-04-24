from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from collections.abc import Callable


class ExceptionHandlerManager:
    """
    A class to manage exception handlers for different exception types.
    This class allows registering handler functions for specific exception types
    and looking up the appropriate handler when an exception occurs.
    Example usage:
    -------------
    handler_manager = ExceptionHandlerManager()
    @handler_manager.exception_handler(ValueError)
    def handle_value_error(e):
        print(f"Handling ValueError: {e}")
        return "Error handled"
    # To handle multiple exception types with the same handler:
    @handler_manager.exception_handler([KeyError, TypeError])
    def handle_multiple_errors(e):
        print(f"Handling {type(e).__name__}: {e}")
        return "Multiple error types handled"
    # To find and execute a handler:
    try:
        # some code that might raise an exception
        raise ValueError("Invalid value")
    except Exception as e:
        handler = handler_manager.lookup_exception_handler(type(e))
        if handler:
            result = handler(e)
    """

    def __init__(self):
        """Initialize an empty dictionary to store exception handlers."""
        self._exception_handlers: dict[type[Exception], Callable] = {}

    def exception_handler(self, exc_class: type[Exception] | list[type[Exception]]):
        """
        A decorator function that registers a handler for one or more exception types.
        Parameters
        ----------
        exc_class : type[Exception] | list[type[Exception]]
            A single exception type or a list of exception types.
        Returns
        -------
        Callable
            A decorator function that registers the exception handler.
        """

        def register_exception_handler(func: Callable):
            if isinstance(exc_class, list):
                for exp in exc_class:
                    self._exception_handlers[exp] = func
            else:
                self._exception_handlers[exc_class] = func
            return func

        return register_exception_handler

    def lookup_exception_handler(self, exp_type: type) -> Callable | None:
        """
        Looks up the registered exception handler for the given exception type or its base classes.
        Parameters
        ----------
        exp_type : type
            The exception type to look up the handler for.
        Returns
        -------
        Callable | None
            The registered exception handler function if found, otherwise None.
        """
        for cls in exp_type.__mro__:
            if cls in self._exception_handlers:
                return self._exception_handlers[cls]
        return None

    def update_exception_handlers(self, handlers: Mapping[type[Exception], Callable]) -> None:
        """
        Updates the exception handlers dictionary with new handler mappings.
        This method allows bulk updates of exception handlers by providing a dictionary
        mapping exception types to handler functions.
        Parameters
        ----------
        handlers : Mapping[Type[Exception], Callable]
            A dictionary mapping exception types to handler functions.
        Example
        -------
        >>> def handle_value_error(e):
        ...     print(f"Value error: {e}")
        ...
        >>> def handle_key_error(e):
        ...     print(f"Key error: {e}")
        ...
        >>> handler_manager.update_exception_handlers({
        ...     ValueError: handle_value_error,
        ...     KeyError: handle_key_error
        ... })
        """
        self._exception_handlers.update(handlers)

    def get_registered_handlers(self) -> dict[type[Exception], Callable]:
        """
        Returns all registered exception handlers.
        Returns
        -------
        Dict[Type[Exception], Callable]
            A dictionary mapping exception types to their handler functions.
        """
        return self._exception_handlers.copy()

    def clear_handlers(self) -> None:
        """
        Clears all registered exception handlers.
        """
        self._exception_handlers.clear()
