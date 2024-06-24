import datetime
import logging
from copy import deepcopy
from typing import Any, Callable, Dict, Optional, Tuple

from aws_lambda_powertools.utilities.idempotency.config import (
    IdempotencyConfig,
)
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
    BasePersistenceLayer,
)
from aws_lambda_powertools.utilities.idempotency.persistence.datarecord import (
    STATUS_CONSTANTS,
    DataRecord,
)
from aws_lambda_powertools.utilities.idempotency.serialization.base import (
    BaseIdempotencySerializer,
)
from aws_lambda_powertools.utilities.idempotency.serialization.no_op import (
    NoOpSerializer,
)

MAX_RETRIES = 2
logger = logging.getLogger(__name__)


def _prepare_data(data: Any) -> Any:
    """Prepare data for json serialization.

    We will convert Python dataclasses, pydantic models or event source data classes to a dict,
    otherwise return data as-is.
    """
    if hasattr(data, "__dataclass_fields__"):
        import dataclasses

        return dataclasses.asdict(data)

    if callable(getattr(data, "dict", None)):
        return data.dict()

    return getattr(data, "raw_event", data)


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
        output_serializer: Optional[BaseIdempotencySerializer] = None,
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
        output_serializer: Optional[BaseIdempotencySerializer]
            Serializer to transform the data to and from a dictionary.
            If not supplied, no serialization is done via the NoOpSerializer
        function_args: Optional[Tuple]
            Function arguments
        function_kwargs: Optional[Dict]
            Function keyword arguments
        """
        self.function = function
        self.output_serializer = output_serializer or NoOpSerializer()
        self.data = deepcopy(_prepare_data(function_payload))
        self.fn_args = function_args
        self.fn_kwargs = function_kwargs
        self.config = config

        persistence_store.configure(config, f"{self.function.__module__}.{self.function.__qualname__}")
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
            self.persistence_store.save_inprogress(
                data=self.data,
                remaining_time_in_millis=self._get_remaining_time_in_millis(),
            )
        except (IdempotencyKeyError, IdempotencyValidationError):
            raise
        except IdempotencyItemAlreadyExistsError as exc:
            # Attempt to retrieve the existing record, either from the exception ReturnValuesOnConditionCheckFailure
            # or perform a GET operation if the information is not available.
            # We give preference to ReturnValuesOnConditionCheckFailure because it is a faster and more cost-effective
            # way of retrieving the existing record after a failed conditional write operation.
            record = exc.old_data_record or self._get_idempotency_record()

            # If a record is found, handle it for status
            if record:
                return self._handle_for_status(record)
        except Exception as exc:
            raise IdempotencyPersistenceLayerError(
                "Failed to save in progress record to idempotency store",
                exc,
            ) from exc

        return self._get_function_response()

    def _get_remaining_time_in_millis(self) -> Optional[int]:
        """
        Tries to determine the remaining time available for the current lambda invocation.

        This only works if the idempotent handler decorator is used, since we need to access the lambda context.
        However, this could be improved if we start storing the lambda context globally during the invocation. One
        way to do this is to register the lambda context when configuring the IdempotencyConfig object.

        Returns
        -------
        Optional[int]
            Remaining time in millis, or None if the remaining time cannot be determined.
        """

        if self.config.lambda_context is not None:
            return self.config.lambda_context.get_remaining_time_in_millis()

        return None

    def _get_idempotency_record(self) -> Optional[DataRecord]:
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
                f"An existing idempotency record was deleted before we could fetch it. Proceeding with {self.function}",
            )
            raise IdempotencyInconsistentStateError("save_inprogress and get_record return inconsistent results.")

        # Allow this exception to bubble up
        except IdempotencyValidationError:
            raise

        # Wrap remaining unhandled exceptions with IdempotencyPersistenceLayerError to ease exception handling for
        # clients
        except Exception as exc:
            raise IdempotencyPersistenceLayerError("Failed to get record from idempotency store", exc) from exc

        return data_record

    def _handle_for_status(self, data_record: DataRecord) -> Optional[Any]:
        """
        Take appropriate action based on data_record's status

        Parameters
        ----------
        data_record: DataRecord

        Returns
        -------
        Optional[Any]
            Function's response previously used for this idempotency key, if it has successfully executed already.
            In case an output serializer is configured, the response is deserialized.

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
            if data_record.in_progress_expiry_timestamp is not None and data_record.in_progress_expiry_timestamp < int(
                datetime.datetime.now().timestamp() * 1000,
            ):
                raise IdempotencyInconsistentStateError(
                    "item should have been expired in-progress because it already time-outed.",
                )

            raise IdempotencyAlreadyInProgressError(
                f"Execution already in progress with idempotency key: "
                f"{self.persistence_store.event_key_jmespath}={data_record.idempotency_key}",
            )
        response_dict: Optional[dict] = data_record.response_json_as_dict()
        if response_dict is not None:
            serialized_response = self.output_serializer.from_dict(response_dict)
            if self.config.response_hook is not None:
                logger.debug("Response hook configured, invoking function")
                return self.config.response_hook(
                    serialized_response,
                    data_record,
                )
            return serialized_response

        return None

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
                    "Failed to delete record from idempotency store",
                    delete_exception,
                ) from delete_exception
            raise

        else:
            try:
                serialized_response: dict = self.output_serializer.to_dict(response) if response else None
                self.persistence_store.save_success(data=self.data, result=serialized_response)
            except Exception as save_exception:
                raise IdempotencyPersistenceLayerError(
                    "Failed to update record state to success in idempotency store",
                    save_exception,
                ) from save_exception

        return response
