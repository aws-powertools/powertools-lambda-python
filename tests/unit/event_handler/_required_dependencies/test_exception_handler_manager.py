import pytest

from aws_lambda_powertools.event_handler.exception_handling import (
    ExceptionHandlerManager,  # Assuming the class is in this module
)


@pytest.fixture
def exception_manager() -> ExceptionHandlerManager:
    """Fixture to provide a fresh ExceptionHandlerManager instance for each test."""
    return ExceptionHandlerManager()


# ----- Tests for exception_handler decorator -----


def test_decorator_registers_single_exception_handler(exception_manager):
    """
    WHEN the exception_handler decorator is used with a single exception type
    GIVEN a function decorated with @manager.exception_handler(ValueError)
    THEN the function is registered as a handler for ValueError
    """

    @exception_manager.exception_handler(ValueError)
    def handle_value_error(e):
        return "ValueError handled"

    handlers = exception_manager.get_registered_handlers()
    assert ValueError in handlers
    assert handlers[ValueError] == handle_value_error


def test_decorator_registers_multiple_exception_handlers(exception_manager):
    """
    GIVEN a function decorated with @manager.exception_handler([KeyError, TypeError])
    WHEN the exception_handler decorator is used with multiple exception types
    THEN the function is registered as a handler for both KeyError and TypeError
    """

    @exception_manager.exception_handler([KeyError, TypeError])
    def handle_multiple_errors(e):
        return f"{type(e).__name__} handled"

    handlers = exception_manager.get_registered_handlers()
    assert KeyError in handlers
    assert TypeError in handlers
    assert handlers[KeyError] == handle_multiple_errors
    assert handlers[TypeError] == handle_multiple_errors


def test_lookup_uses_inheritance_hierarchy(exception_manager):
    # GIVEN a handler has been registered for a base exception type
    @exception_manager.exception_handler(Exception)
    def handle_exception(e):
        return "Exception handled"

    # WHEN lookup_exception_handler is called with a derived exception type
    # THEN the handler for the base exception is returned
    handler = exception_manager.lookup_exception_handler(ValueError)
    assert handler == handle_exception


def test_lookup_returns_none_for_unregistered_handler(exception_manager):
    """
    GIVEN no handler has been registered for that type or its base classes
    WHEN lookup_exception_handler is called with an exception type
    THEN None is returned
    """
    handler = exception_manager.lookup_exception_handler(ValueError)
    assert handler is None


def test_register_handler_for_multiple_exceptions(exception_manager):
    # GIVEN a valid handler function
    @exception_manager.exception_handler([ValueError, KeyError])
    def handle_error(e):
        return "Error handled"

    # THEN the handler is properly registered for all exceptions in the list
    handlers = exception_manager.get_registered_handlers()
    assert KeyError in handlers
    assert ValueError in handlers
    assert handlers[KeyError] == handle_error
    assert handlers[ValueError] == handle_error


def test_update_exception_handlers_with_dictionary(exception_manager):
    """
    WHEN update_exception_handlers is called with a dictionary
    GIVEN the dictionary maps exception types to handler functions
    THEN all handlers in the dictionary are properly registered
    """

    def handle_value_error(e):
        return "ValueError handled"

    def handle_key_error(e):
        return "KeyError handled"

    # Update with a dictionary of handlers
    exception_manager.update_exception_handlers(
        {
            ValueError: handle_value_error,
            KeyError: handle_key_error,
        },
    )

    handlers = exception_manager.get_registered_handlers()
    assert ValueError in handlers
    assert KeyError in handlers
    assert handlers[ValueError] == handle_value_error
    assert handlers[KeyError] == handle_key_error


def test_clear_handlers_removes_all_handlers(exception_manager):
    # GIVEN handlers have been registered
    @exception_manager.exception_handler([ValueError, KeyError])
    def handle_error(e):
        return "Error handled"

    # Verify handlers are registered
    assert len(exception_manager.get_registered_handlers()) == 2

    # WHEN clear_handlers is called
    exception_manager.clear_handlers()

    # THEN all handlers are removed
    assert len(exception_manager.get_registered_handlers()) == 0


def test_get_registered_handlers_returns_copy(exception_manager):
    # WHEN get_registered_handlers is called
    @exception_manager.exception_handler(ValueError)
    def handle_error(e):
        return "Error handled"

    # GIVEN handlers have been registered
    handlers_copy = exception_manager.get_registered_handlers()

    # THEN a copy of the handlers dictionary is returned that doesn't affect the original
    handlers_copy[KeyError] = lambda e: "Not registered properly"
    assert KeyError not in exception_manager.get_registered_handlers()


def test_handler_executes_correctly(exception_manager):
    # GIVEN a registered handler is executed with an exception
    @exception_manager.exception_handler(ValueError)
    def handle_value_error(e):
        return f"Handled: {str(e)}"

    # WHEN an exception happens
    # THEN the handler processes the exception correctly
    try:
        raise ValueError("Test error")
    except Exception as e:
        handler = exception_manager.lookup_exception_handler(type(e))
        result = handler(e)
        assert result == "Handled: Test error"


def test_registering_new_handler_overrides_previous(exception_manager):
    # WHEN a new handler is registered for an exception type
    @exception_manager.exception_handler(ValueError)
    def first_handler(e):
        return "First handler"

    # GIVEN a handler was already registered for that type
    @exception_manager.exception_handler(ValueError)
    def second_handler(e):
        return "Second handler"

    # THEN the new handler replaces the previous one
    # Check that the second handler overrode the first
    handler = exception_manager.lookup_exception_handler(ValueError)
    assert handler == second_handler
    assert handler != first_handler
