"""
Primary interface for idempotent Lambda functions utility
"""
import logging
from typing import Any, Callable, Dict, Optional

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.idempotency.config import IdempotencyConfig
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyAlreadyInProgressError,
    IdempotencyInconsistentStateError,
    IdempotencyItemAlreadyExistsError,
    IdempotencyItemNotFoundError,
    IdempotencyPersistenceLayerError,
    IdempotencyValidationError,
)
from aws_lambda_powertools.utilities.idempotency.persistence.base import (
    STATUS_CONSTANTS,
    BasePersistenceLayer,
    DataRecord,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = logging.getLogger(__name__)


@lambda_handler_decorator
def idempotent(
    handler: Callable[[Any, LambdaContext], Any],
    event: Dict[str, Any],
    context: LambdaContext,
    persistence_store: BasePersistenceLayer,
    config: IdempotencyConfig = None,
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
    idempotency_handler = IdempotencyHandler(
        lambda_handler=handler, event=event, context=context, persistence_store=persistence_store, config=config
    )

    # IdempotencyInconsistentStateError can happen under rare but expected cases when persistent state changes in the
    # small time between put & get requests. In most cases we can retry successfully on this exception.
    # Maintenance: Allow customers to specify number of retries
    max_handler_retries = 2
    for i in range(max_handler_retries + 1):
        try:
            return idempotency_handler.handle()
        except IdempotencyInconsistentStateError:
            if i < max_handler_retries:
                continue
            else:
                # Allow the exception to bubble up after max retries exceeded
                raise


class IdempotencyHandler:
    """
    Class to orchestrate calls to persistence layer.
    """

    def __init__(
        self,
        lambda_handler: Callable[[Any, LambdaContext], Any],
        event: Dict[str, Any],
        context: LambdaContext,
        config: IdempotencyConfig,
        persistence_store: BasePersistenceLayer,
    ):
        """
        Initialize the IdempotencyHandler

        Parameters
        ----------
        lambda_handler : Callable[[Any, LambdaContext], Any]
            Lambda function handler
        event : Dict[str, Any]
            Event payload lambda handler will be called with
        context : LambdaContext
            Context object which will be passed to lambda handler
        persistence_store : BasePersistenceLayer
            Instance of persistence layer to store idempotency records
        """
        persistence_store.configure(config)
        self.persistence_store = persistence_store
        self.context = context
        self.event = event
        self.lambda_handler = lambda_handler
        self.max_handler_retries = 2

    def handle(self) -> Any:
        """
        Main entry point for handling idempotent execution of lambda handler.

        Returns
        -------
        Any
            lambda handler response

        """
        try:
            # We call save_inprogress first as an optimization for the most common case where no idempotent record
            # already exists. If it succeeds, there's no need to call get_record.
            self.persistence_store.save_inprogress(event=self.event, context=self.context)
        except IdempotencyItemAlreadyExistsError:
            # Now we know the item already exists, we can retrieve it
            record = self._get_idempotency_record()
            return self._handle_for_status(record)
        except Exception as exc:
            raise IdempotencyPersistenceLayerError("Failed to save in progress record to idempotency store") from exc

        return self._call_lambda_handler()

    def _get_idempotency_record(self) -> DataRecord:
        """
        Retrieve the idempotency record from the persistence layer.

        Raises
        ----------
        IdempotencyInconsistentStateError

        """
        try:
            event_record = self.persistence_store.get_record(event=self.event, context=self.context)
        except IdempotencyItemNotFoundError:
            # This code path will only be triggered if the record is removed between save_inprogress and get_record.
            logger.debug(
                "An existing idempotency record was deleted before we could retrieve it. Proceeding with lambda "
                "handler"
            )
            raise IdempotencyInconsistentStateError("save_inprogress and get_record return inconsistent results.")

        # Allow this exception to bubble up
        except IdempotencyValidationError:
            raise

        # Wrap remaining unhandled exceptions with IdempotencyPersistenceLayerError to ease exception handling for
        # clients
        except Exception as exc:
            raise IdempotencyPersistenceLayerError("Failed to get record from idempotency store") from exc

        return event_record

    def _handle_for_status(self, event_record: DataRecord) -> Optional[Dict[Any, Any]]:
        """
        Take appropriate action based on event_record's status

        Parameters
        ----------
        event_record: DataRecord

        Returns
        -------
        Optional[Dict[Any, Any]
            Lambda response previously used for this idempotency key, if it has successfully executed already.

        Raises
        ------
        AlreadyInProgressError
            A lambda execution is already in progress
        IdempotencyInconsistentStateError
            The persistence store reports inconsistent states across different requests. Retryable.
        """
        # This code path will only be triggered if the record becomes expired between the save_inprogress call and here
        if event_record.status == STATUS_CONSTANTS["EXPIRED"]:
            raise IdempotencyInconsistentStateError("save_inprogress and get_record return inconsistent results.")

        if event_record.status == STATUS_CONSTANTS["INPROGRESS"]:
            raise IdempotencyAlreadyInProgressError(
                f"Execution already in progress with idempotency key: "
                f"{self.persistence_store.event_key_jmespath}={event_record.idempotency_key}"
            )

        return event_record.response_json_as_dict()

    def _call_lambda_handler(self) -> Any:
        """
        Call the lambda handler function and update the persistence store appropriate depending on the output

        Returns
        -------
        Any
            lambda handler response

        """
        try:
            handler_response = self.lambda_handler(self.event, self.context)
        except Exception as handler_exception:
            # We need these nested blocks to preserve lambda handler exception in case the persistence store operation
            # also raises an exception
            try:
                self.persistence_store.delete_record(
                    event=self.event, context=self.context, exception=handler_exception
                )
            except Exception as delete_exception:
                raise IdempotencyPersistenceLayerError(
                    "Failed to delete record from idempotency store"
                ) from delete_exception
            raise

        else:
            try:
                self.persistence_store.save_success(event=self.event, context=self.context, result=handler_response)
            except Exception as save_exception:
                raise IdempotencyPersistenceLayerError(
                    "Failed to update record state to success in idempotency store"
                ) from save_exception

        return handler_response
