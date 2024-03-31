from typing import Any, Dict, Optional

from aws_lambda_powertools.shared.types import Protocol
from aws_lambda_powertools.utilities.idempotency.persistence.datarecord import DataRecord
from aws_lambda_powertools.utilities.typing import LambdaContext


class IdempotentHookData:
    """
    Idempotent Hook Data

    Contains data relevant to the current Idempotent record which matches the current request.
    All IdempotentHook functions will be passed this data as well as the current Response.
    """

    def __init__(self, data_record: DataRecord) -> None:
        self._idempotency_key = data_record.idempotency_key
        self._status = data_record.status
        self._expiry_timestamp = data_record.expiry_timestamp

    @property
    def idempotency_key(self) -> str:
        return self._idempotency_key

    @property
    def status(self) -> str:
        return self._status

    @property
    def expiry_timestamp(self) -> Optional[int]:
        return self._expiry_timestamp


class IdempotentHookFunction(Protocol):
    """
    The IdempotentHookFunction.
    This class defines the calling signature for IdempotentHookFunction callbacks.
    """

    def __call__(self, response: Any, idempotent_data: IdempotentHookData) -> Any: ...


class IdempotencyConfig:
    def __init__(
        self,
        event_key_jmespath: str = "",
        payload_validation_jmespath: str = "",
        jmespath_options: Optional[Dict] = None,
        raise_on_no_idempotency_key: bool = False,
        expires_after_seconds: int = 60 * 60,  # 1 hour default
        use_local_cache: bool = False,
        local_cache_max_items: int = 256,
        hash_function: str = "md5",
        lambda_context: Optional[LambdaContext] = None,
        response_hook: Optional[IdempotentHookFunction] = None,
    ):
        """
        Initialize the base persistence layer

        Parameters
        ----------
        event_key_jmespath: str
            A jmespath expression to extract the idempotency key from the event record
        payload_validation_jmespath: str
            A jmespath expression to extract the payload to be validated from the event record
        raise_on_no_idempotency_key: bool, optional
            Raise exception if no idempotency key was found in the request, by default False
        expires_after_seconds: int
            The number of seconds to wait before a record is expired
        use_local_cache: bool, optional
            Whether to locally cache idempotency results, by default False
        local_cache_max_items: int, optional
            Max number of items to store in local cache, by default 1024
        hash_function: str, optional
            Function to use for calculating hashes, by default md5.
        lambda_context: LambdaContext, optional
            Lambda Context containing information about the invocation, function and execution environment.
        response_hook: IdempotentHookFunction, optional
            Hook function to be called when an idempotent response is returned from the idempotent store.
        """
        self.event_key_jmespath = event_key_jmespath
        self.payload_validation_jmespath = payload_validation_jmespath
        self.jmespath_options = jmespath_options
        self.raise_on_no_idempotency_key = raise_on_no_idempotency_key
        self.expires_after_seconds = expires_after_seconds
        self.use_local_cache = use_local_cache
        self.local_cache_max_items = local_cache_max_items
        self.hash_function = hash_function
        self.lambda_context: Optional[LambdaContext] = lambda_context
        self.response_hook: Optional[IdempotentHookFunction] = response_hook

    def register_lambda_context(self, lambda_context: LambdaContext):
        """Captures the Lambda context, to calculate the remaining time before the invocation times out"""
        self.lambda_context = lambda_context
