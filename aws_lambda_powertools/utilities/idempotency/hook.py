from typing import Any

from aws_lambda_powertools.shared.types import Protocol
from aws_lambda_powertools.utilities.idempotency.persistence.datarecord import DataRecord


class IdempotentHookFunction(Protocol):
    """
    The IdempotentHookFunction.
    This class defines the calling signature for IdempotentHookFunction callbacks.
    """

    def __call__(self, response: Any, idempotent_data: DataRecord) -> Any: ...
