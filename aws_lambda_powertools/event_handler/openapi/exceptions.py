from typing import Any, Sequence


class ValidationException(Exception):
    """
    Base exception for all validation errors
    """

    def __init__(self, errors: Sequence[Any]) -> None:
        self._errors = errors

    def errors(self) -> Sequence[Any]:
        return self._errors


class RequestValidationError(ValidationException):
    """
    Raised when the request body does not match the OpenAPI schema
    """

    def __init__(self, errors: Sequence[Any], *, body: Any = None) -> None:
        super().__init__(errors)
        self.body = body


class SerializationError(Exception):
    """
    Base exception for all encoding errors
    """


class SchemaValidationError(ValidationException):
    """
    Raised when the OpenAPI schema validation fails
    """
