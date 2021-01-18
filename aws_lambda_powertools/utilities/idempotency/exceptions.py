"""
Idempotency errors
"""


class ItemAlreadyExistsError(Exception):
    """
    Item attempting to be inserted into persistence store already exists
    """


class ItemNotFoundError(Exception):
    """
    Item does not exist in persistence store
    """


class AlreadyInProgressError(Exception):
    """
    Execution with idempotency key is already in progress
    """


class InvalidStatusError(Exception):
    """
    An invalid status was provided
    """


class IdempotencyValidationerror(Exception):
    """
    Payload does not match stored idempotency record
    """
