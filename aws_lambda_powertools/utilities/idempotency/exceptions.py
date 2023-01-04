"""
Idempotency errors
"""


class BaseError(Exception):
    """
    Base error class that overwrites the way exception and extra information is printed.
    See https://github.com/awslabs/aws-lambda-powertools-python/issues/1772
    """

    def format_msg(self, *args: str) -> str:
        full_msg = str(args[0])
        if args[1:]:
            full_msg += f': ({"".join(str(arg) for arg in args[1:])})'
        return full_msg

    def __init__(self, *args: str):
        if args:
            super().__init__(self.format_msg(*args))
        else:
            super().__init__()


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
