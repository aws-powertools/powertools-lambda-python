"""
Idempotency errors
"""


from typing import Optional, Union


class BaseError(Exception):
    """
    Base error class that overwrites the way exception and extra information is printed.
    See https://github.com/awslabs/aws-lambda-powertools-python/issues/1772
    """

    def __init__(self, *args: Optional[Union[str, Exception]]):
        self.message = str(args[0]) if args else ""
        self.details = "".join(str(arg) for arg in args[1:]) if args[1:] else None

    def __str__(self):
        """
        Return all arguments formatted or original message
        """
        if self.message and self.details:
            return f"{self.message} - ({self.details})"
        return self.message


class IdempotencyItemAlreadyExistsError(BaseError):
    """
    Item attempting to be inserted into persistence store already exists and is not expired
    """


class IdempotencyItemNotFoundError(BaseError):
    """
    Item does not exist in persistence store
    """


class IdempotencyAlreadyInProgressError(BaseError):
    """
    Execution with idempotency key is already in progress
    """


class IdempotencyInvalidStatusError(BaseError):
    """
    An invalid status was provided
    """


class IdempotencyValidationError(BaseError):
    """
    Payload does not match stored idempotency record
    """


class IdempotencyInconsistentStateError(BaseError):
    """
    State is inconsistent across multiple requests to persistence store
    """


class IdempotencyPersistenceLayerError(BaseError):
    """
    Unrecoverable error from the data store
    """


class IdempotencyKeyError(BaseError):
    """
    Payload does not contain an idempotent key
    """
