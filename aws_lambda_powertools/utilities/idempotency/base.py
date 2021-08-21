import logging
from typing import Any, Callable, Dict, Optional, Tuple

from aws_lambda_powertools.utilities.idempotency.config import IdempotencyConfig
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyAlreadyInProgressError,
    IdempotencyInconsistentStateError,
    IdempotencyItemAlreadyExistsError,
    IdempotencyItemNotFoundError,
    IdempotencyKeyError,
    IdempotencyPersistenceLayerError,
    IdempotencyValidationError,
)
from aws_lambda_powertools.utilities.idempotency.persistence.base import (
    STATUS_CONSTANTS,
    BasePersistenceLayer,
    DataRecord,
)

MAX_RETRIES = 2
logger = logging.getLogger(__name__)


class IdempotencyHandler:
    """
    Base class to orchestrate calls to persistence layer.
    """

    def __init__(
        self,
        function: Callable,
        function_payload: Any,
        config: IdempotencyConfig,
        persistence_store: BasePersistenceLayer,
        function_args: Optional[Tuple] = None,
        function_kwargs: Optional[Dict] = None,
    ):
        """
        Initialize the IdempotencyHandler

        Parameters
        ----------
        function_payload: Any
            JSON Serializable payload to be hashed
        config: IdempotencyConfig
            Idempotency Configuration
        persistence_store : BasePersistenceLayer
            Instance of persistence layer to store idempotency records
        function_args: Optional[Tuple]
            Function arguments
        function_kwargs: Optional[Dict]
            Function keyword arguments
        """
        self.function = function
        self.data = function_payload
        self.fn_args = function_args
        self.fn_kwargs = function_kwargs

        persistence_store.configure(config)
        self.persistence_store = persistence_store

    def handle(self) -> Any:
        """
        Main entry point for handling idempotent execution of a function.

        Returns
        -------
        Any
            Function response

        """
        # IdempotencyInconsistentStateError can happen under rare but expected cases
        # when persistent state changes in the small time between put & get requests.
        # In most cases we can retry successfully on this exception.
        for i in range(MAX_RETRIES + 1):  # pragma: no cover
            try:
                return self._process_idempotency()
            except IdempotencyInconsistentStateError:
                if i == MAX_RETRIES:
                    raise  # Bubble up when exceeded max tries

    def _process_idempotency(self):
        try:
            # We call save_inprogress first as an optimization for the most common case where no idempotent record
            # already exists. If it succeeds, there's no need to call get_record.
            self.persistence_store.save_inprogress(data=self.data)
        except IdempotencyKeyError:
            raise
        except IdempotencyItemAlreadyExistsError:
            # Now we know the item already exists, we can retrieve it
            record = self._get_idempotency_record()
            return self._handle_for_status(record)
        except Exception as exc:
            raise IdempotencyPersistenceLayerError("Failed to save in progress record to idempotency store") from exc

        return self._get_function_response()

    def _get_idempotency_record(self) -> DataRecord:
        """
        Retrieve the idempotency record from the persistence layer.

        Raises
        ----------
        IdempotencyInconsistentStateError

        """
        try:
            data_record = self.persistence_store.get_record(data=self.data)
        except IdempotencyItemNotFoundError:
            # This code path will only be triggered if the record is removed between save_inprogress and get_record.
            logger.debug(
                f"An existing idempotency record was deleted before we could fetch it. Proceeding with {self.function}"
            )
            raise IdempotencyInconsistentStateError("save_inprogress and get_record return inconsistent results.")

        # Allow this exception to bubble up
        except IdempotencyValidationError:
            raise

        # Wrap remaining unhandled exceptions with IdempotencyPersistenceLayerError to ease exception handling for
        # clients
        except Exception as exc:
            raise IdempotencyPersistenceLayerError("Failed to get record from idempotency store") from exc

        return data_record

    def _handle_for_status(self, data_record: DataRecord) -> Optional[Dict[Any, Any]]:
        """
        Take appropriate action based on data_record's status

        Parameters
        ----------
        data_record: DataRecord

        Returns
        -------
        Optional[Dict[Any, Any]
            Function's response previously used for this idempotency key, if it has successfully executed already.

        Raises
        ------
        AlreadyInProgressError
            A function execution is already in progress
        IdempotencyInconsistentStateError
            The persistence store reports inconsistent states across different requests. Retryable.
        """
        # This code path will only be triggered if the record becomes expired between the save_inprogress call and here
        if data_record.status == STATUS_CONSTANTS["EXPIRED"]:
            raise IdempotencyInconsistentStateError("save_inprogress and get_record return inconsistent results.")

        if data_record.status == STATUS_CONSTANTS["INPROGRESS"]:
            raise IdempotencyAlreadyInProgressError(
                f"Execution already in progress with idempotency key: "
                f"{self.persistence_store.event_key_jmespath}={data_record.idempotency_key}"
            )

        return data_record.response_json_as_dict()

    def _get_function_response(self):
        try:
            response = self.function(*self.fn_args, **self.fn_kwargs)
        except Exception as handler_exception:
            # We need these nested blocks to preserve function's exception in case the persistence store operation
            # also raises an exception
            try:
                self.persistence_store.delete_record(data=self.data, exception=handler_exception)
            except Exception as delete_exception:
                raise IdempotencyPersistenceLayerError(
                    "Failed to delete record from idempotency store"
                ) from delete_exception
            raise

        else:
            try:
                self.persistence_store.save_success(data=self.data, result=response)
            except Exception as save_exception:
                raise IdempotencyPersistenceLayerError(
                    "Failed to update record state to success in idempotency store"
                ) from save_exception

        return response
