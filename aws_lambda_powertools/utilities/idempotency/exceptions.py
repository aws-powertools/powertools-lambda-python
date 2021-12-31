"""
Idempotency errors
"""


class IdempotencyItemAlreadyExistsError(Exception):
    """
    Item attempting to be inserted into persistence store already exists and is not expired
    """


class IdempotencyItemNotFoundError(Exception):
    """
    Item does not exist in persistence store
    """


class IdempotencyAlreadyInProgressError(Exception):
    """
    Execution with idempotency key is already in progress
    """


class IdempotencyInvalidStatusError(Exception):
    """
    An invalid status was provided
    """


class IdempotencyValidationError(Exception):
    """
    Payload does not match stored idempotency record
    """


class IdempotencyInconsistentStateError(Exception):
    """
    State is inconsistent across multiple requests to persistence store
    """


class IdempotencyPersistenceLayerError(Exception):
    """
    Unrecoverable error from the data store
    """


class IdempotencyKeyError(Exception):
    """
    Payload does not contain an idempotent key
    """
