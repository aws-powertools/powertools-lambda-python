"""
Primary interface for idempotent Lambda functions utility
"""
import logging
from typing import Any, Callable, Dict, Optional

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.idempotency.base import IdempotencyHandler
from aws_lambda_powertools.utilities.idempotency.config import IdempotencyConfig
from aws_lambda_powertools.utilities.idempotency.exceptions import IdempotencyInconsistentStateError
from aws_lambda_powertools.utilities.idempotency.persistence.base import BasePersistenceLayer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = logging.getLogger(__name__)


@lambda_handler_decorator
def idempotent(
    handler: Callable[[Any, LambdaContext], Any],
    event: Dict[str, Any],
    context: LambdaContext,
    persistence_store: BasePersistenceLayer,
    config: Optional[IdempotencyConfig] = None,
    **kwargs
) -> Any:
    """
    Middleware to handle idempotency

    Parameters
    ----------
    handler: Callable
        Lambda's handler
    event: Dict
        Lambda's Event
    context: Dict
        Lambda's Context
    persistence_store: BasePersistenceLayer
        Instance of BasePersistenceLayer to store data
    config: IdempotencyConfig
        Configuration

    Examples
    --------
    **Processes Lambda's event in an idempotent manner**

        >>> from aws_lambda_powertools.utilities.idempotency import (
        >>>    idempotent, DynamoDBPersistenceLayer, IdempotencyConfig
        >>> )
        >>>
        >>> idem_config=IdempotencyConfig(event_key_jmespath="body")
        >>> persistence_layer = DynamoDBPersistenceLayer(table_name="idempotency_store")
        >>>
        >>> @idempotent(config=idem_config, persistence_store=persistence_layer)
        >>> def handler(event, context):
        >>>     return {"StatusCode": 200}
    """

    config = config or IdempotencyConfig()
    args = event, context
    idempotency_handler = IdempotencyHandler(
        function=handler,
        function_payload=event,
        idempotency_config=config,
        persistence_store=persistence_store,
        function_args=args,
        function_kwargs=kwargs,
    )

    # IdempotencyInconsistentStateError can happen under rare but expected cases when persistent state changes in the
    # small time between put & get requests. In most cases we can retry successfully on this exception.
    # Maintenance: Allow customers to specify number of retries
    max_handler_retries = 2
    for i in range(max_handler_retries + 1):
        try:
            return idempotency_handler.handle()
        except IdempotencyInconsistentStateError:
            if i == max_handler_retries:
                # Allow the exception to bubble up after max retries exceeded
                raise
