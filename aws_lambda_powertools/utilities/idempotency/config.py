from typing import Dict, Optional

from aws_lambda_powertools.utilities.typing import LambdaContext


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

    def register_lambda_context(self, lambda_context: LambdaContext):
        """Captures the Lambda context, to calculate the remaining time before the invocation times out"""
        self.lambda_context = lambda_context
