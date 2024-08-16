"""
Idempotency errors
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.idempotency.persistence.datarecord import DataRecord


class BaseError(Exception):
    """
    Base error class that overwrites the way exception and extra information is printed.
    See https://github.com/aws-powertools/powertools-lambda-python/issues/1772
    """

    def __init__(self, *args: str | Exception | None):
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

    def __init__(self, *args: str | Exception | None, old_data_record: DataRecord | None = None):
        self.old_data_record = old_data_record
        super().__init__(*args)

    def __str__(self):
        """
        Return all arguments formatted or original message
        """
        old_data_record = f" from [{(str(self.old_data_record))}]" if self.old_data_record else ""
        message = super().__str__()
        return f"{message}{old_data_record}"


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


class IdempotencyModelTypeError(BaseError):
    """
    Model type does not match expected payload output
    """


class IdempotencyNoSerializationModelError(BaseError):
    """
    No model was supplied to the serializer
    """


class IdempotencyPersistenceConfigError(BaseError):
    """
    The idempotency persistency configuration was unsupported
    """


class IdempotencyPersistenceConnectionError(BaseError):
    """
    Idempotency persistence connection error
    """


class IdempotencyPersistenceConsistencyError(BaseError):
    """
    Idempotency persistency consistency error, needs to be removed
    """
