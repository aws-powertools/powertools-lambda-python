"""
Persistence layers supporting idempotency
"""

import datetime
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

import jmespath

from aws_lambda_powertools.utilities.idempotency.cache_dict import LRUDict
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyValidationerror,
    InvalidStatusError,
    ItemAlreadyExistsError,
)

logger = logging.getLogger(__name__)

STATUS_CONSTANTS = {
    "NOTEXISTING": "DOESNOTEXIST",
    "INPROGRESS": "INPROGRESS",
    "COMPLETED": "COMPLETED",
    "EXPIRED": "EXPIRED",
    "ERROR": "ERROR",
}


class DataRecord:
    """
    Data Class for idempotency records.
    """

    def __init__(
        self,
        idempotency_key,
        status: str = "",
        expiry_timestamp: int = None,
        response_data: str = "",
        payload_hash: str = None,
    ) -> None:
        """

        Parameters
        ----------
        idempotency_key: str
            hashed representation of the idempotent data
        status: str, optional
            status of the idempotent record
        expiry_timestamp: int, optional
            time before the record should expire, in milliseconds
        payload_hash: str, optional
            hashed representation of payload
        response_data: str, optional
            response data from previous executions using the record
        """
        self.idempotency_key = idempotency_key
        self.payload_hash = payload_hash
        self.expiry_timestamp = expiry_timestamp
        self._status = status
        self.response_data = response_data

    @property
    def is_expired(self) -> bool:
        """
        Check if data record is expired

        Returns
        -------
        bool
            Whether the record is currently expired or not
        """
        if self.expiry_timestamp:
            if int(datetime.datetime.now().timestamp()) > self.expiry_timestamp:
                return True
        return False

    @property
    def status(self) -> str:
        """
        Get status of data record

        Returns
        -------
        str
        """
        if self.is_expired:
            return STATUS_CONSTANTS["EXPIRED"]

        if self._status in STATUS_CONSTANTS.values():
            return self._status
        else:
            raise InvalidStatusError(self._status)

    def response_json_as_dict(self) -> dict:
        """
        Get response data deserialized to python dict

        Returns
        -------
        dict
            previous response data deserialized
        """
        return json.loads(self.response_data)


class BasePersistenceLayer(ABC):
    """
    Abstract Base Class for Idempotency persistence layer.
    """

    def __init__(
        self,
        event_key_jmespath: str,
        payload_validation_jmespath: str = "",
        expires_after: int = 3600,
        use_local_cache: bool = False,
        local_cache_maxsize: int = 1024,
        hash_function: str = "md5",
    ) -> None:
        """
        Initialize the base persistence layer

        Parameters
        ----------
        event_key_jmespath: str
            A jmespath expression to extract the idempotency key from the event record
        payload_validation_jmespath: str
            A jmespath expression to extract the payload to be validated from the event record
        expires_after: int
            The number of milliseconds to wait before a record is expired
        use_local_cache: bool, optional
            Whether to locally cache idempotency results, by default False
        local_cache_maxsize: int, optional
            Max number of items to store in local cache, by default 1024
        hash_function: str, optional
            Function to use for calculating hashes, by default md5.
        """
        self.event_key = event_key_jmespath
        self.event_key_jmespath = jmespath.compile(event_key_jmespath)
        self.expires_after = expires_after
        self.use_local_cache = use_local_cache
        if self.use_local_cache:
            self._cache = LRUDict(max_size=local_cache_maxsize)
        self.payload_validation_enabled = False
        if payload_validation_jmespath:
            self.validation_key_jmespath = jmespath.compile(payload_validation_jmespath)
            self.payload_validation_enabled = True
        self.hash_function = hash_function

    def _get_hashed_idempotency_key(self, lambda_event: Dict[str, Any]) -> str:
        """
        Extract data from lambda event using event key jmespath, and return a hashed representation

        Parameters
        ----------
        lambda_event: Dict[str, Any]
            Lambda event

        Returns
        -------
        str
            Hashed representation of the data extracted by the jmespath expression

        """
        data = self.event_key_jmespath.search(lambda_event)
        return self._generate_hash(data)

    def _get_hashed_payload(self, lambda_event: Dict[str, Any]) -> str:
        """
        Extract data from lambda event using validation key jmespath, and return a hashed representation

        Parameters
        ----------
        lambda_event: Dict[str, Any]
            Lambda event

        Returns
        -------
        str
            Hashed representation of the data extracted by the jmespath expression

        """
        if not self.payload_validation_enabled:
            return ""
        data = self.validation_key_jmespath.search(lambda_event)
        return self._generate_hash(data)

    def _generate_hash(self, data: Any) -> str:
        """
        Generate a hash value from the provided data

        Parameters
        ----------
        data: Any
            The data to hash

        Returns
        -------
        str
            Hashed representation of the provided data

        """
        hash_func = getattr(hashlib, self.hash_function)
        hashed_data = hash_func(json.dumps(data).encode())
        return hashed_data.hexdigest()

    def _validate_payload(self, lambda_event: Dict[str, Any], data_record: DataRecord) -> None:
        """
        Validate that the hashed payload matches in the lambda event and stored data record

        Parameters
        ----------
        lambda_event: Dict[str, Any]
            Lambda event
        data_record: DataRecord
            DataRecord instance

        """
        if self.payload_validation_enabled:
            lambda_payload_hash = self._get_hashed_payload(lambda_event)
            if not data_record.payload_hash == lambda_payload_hash:
                raise IdempotencyValidationerror("Payload does not match stored record for this event key")

    def _get_expiry_timestamp(self) -> int:
        """

        Returns
        -------
        int
            unix timestamp of expiry date for idempotency record

        """
        now = datetime.datetime.now()
        period = datetime.timedelta(seconds=self.expires_after)
        return int((now + period).timestamp())

    def _save_to_cache(self, data_record: DataRecord):
        self._cache[data_record.idempotency_key] = data_record

    def _retrieve_from_cache(self, idempotency_key: str):
        cached_record = self._cache.get(idempotency_key)
        if cached_record:
            if cached_record.is_expired:
                logger.debug(f"Removing expired local cache record for idempotency key: {idempotency_key}")
                self._delete_from_cache(idempotency_key)
            else:
                return cached_record

    def _delete_from_cache(self, idempotency_key: str):
        del self._cache[idempotency_key]

    def save_success(self, event: Dict[str, Any], result: dict) -> None:
        """
        Save record of function's execution completing succesfully

        Parameters
        ----------
        event: Dict[str, Any]
            Lambda event
        result: dict
            The response from lambda handler
        """
        response_data = json.dumps(result)

        data_record = DataRecord(
            idempotency_key=self._get_hashed_idempotency_key(event),
            status=STATUS_CONSTANTS["COMPLETED"],
            expiry_timestamp=self._get_expiry_timestamp(),
            response_data=response_data,
            payload_hash=self._get_hashed_payload(event),
        )
        logger.debug(
            f"Lambda successfully executed. Saving record to persistence store with "
            f"idempotency key: {data_record.idempotency_key}"
        )
        self._update_record(data_record=data_record)

        if self.use_local_cache:
            self._save_to_cache(data_record)

    def save_inprogress(self, event: Dict[str, Any]) -> None:
        """
        Save record of function's execution being in progress

        Parameters
        ----------
        event: Dict[str, Any]
            Lambda event
        """
        data_record = DataRecord(
            idempotency_key=self._get_hashed_idempotency_key(event),
            status=STATUS_CONSTANTS["INPROGRESS"],
            expiry_timestamp=self._get_expiry_timestamp(),
            payload_hash=self._get_hashed_payload(event),
        )

        logger.debug(f"Saving in progress record for idempotency key: {data_record.idempotency_key}")

        if self.use_local_cache:
            record = self._retrieve_from_cache(idempotency_key=data_record.idempotency_key)
            if record:
                raise ItemAlreadyExistsError

        self._put_record(data_record)

        # This has to come after _put_record. If _put_record call raises ItemAlreadyExists we shouldn't populate the
        # cache with an "INPROGRESS" record as we don't know the status in the data store at this point.
        if self.use_local_cache:
            self._save_to_cache(data_record)

    def save_error(self, event: Dict[str, Any], exception: Exception):
        """
        Save record of lambda handler raising an exception

        Parameters
        ----------
        event: Dict[str, Any]
            Lambda event
        exception
            The exception raised by the lambda handler
        """
        data_record = DataRecord(idempotency_key=self._get_hashed_idempotency_key(event))

        logger.debug(
            f"Lambda raised an exception ({type(exception).__name__}). Clearing in progress record in persistence "
            f"store for idempotency key: {data_record.idempotency_key}"
        )
        self._delete_record(data_record)

        if self.use_local_cache:
            self._delete_from_cache(data_record.idempotency_key)

    def get_record(self, lambda_event) -> DataRecord:
        """
        Calculate idempotency key for lambda_event, then retrieve item from persistence store using idempotency key
        and return it as a DataRecord instance.and return it as a DataRecord instance.

        Parameters
        ----------
        lambda_event: Dict[str, Any]

        Returns
        -------
        DataRecord
            DataRecord representation of existing record found in persistence store

        Raises
        ------
        ItemNotFound
            Exception raised if no record exists in persistence store with the idempotency key
        """

        idempotency_key = self._get_hashed_idempotency_key(lambda_event)

        if self.use_local_cache:
            cached_record = self._retrieve_from_cache(idempotency_key)
            if cached_record:
                logger.debug(f"Idempotency record found in cache with idempotency key: {idempotency_key}")
                self._validate_payload(lambda_event, cached_record)
                return cached_record

        record = self._get_record(idempotency_key)

        if self.use_local_cache:
            self._save_to_cache(data_record=record)

        self._validate_payload(lambda_event, record)
        return record

    @abstractmethod
    def _get_record(self, idempotency_key) -> DataRecord:
        """
        Retrieve item from persistence store using idempotency key and return it as a DataRecord instance.

        Parameters
        ----------
        idempotency_key

        Returns
        -------
        DataRecord
            DataRecord representation of existing record found in persistence store

        Raises
        ------
        ItemNotFound
            Exception raised if no record exists in persistence store with the idempotency key
        """
        raise NotImplementedError

    @abstractmethod
    def _put_record(self, data_record: DataRecord) -> None:
        """
        Add a DataRecord to persistence store if it does not already exist with that key. Raise ItemAlreadyExists
        if an entry already exists.

        Parameters
        ----------
        data_record: DataRecord
            DataRecord instance
        """

        raise NotImplementedError

    @abstractmethod
    def _update_record(self, data_record: DataRecord) -> None:
        """
        Update item in persistence store

        Parameters
        ----------
        data_record: DataRecord
            DataRecord instance
        """

        raise NotImplementedError

    @abstractmethod
    def _delete_record(self, data_record: DataRecord) -> None:
        """
        Remove item from persistence store
        Parameters
        ----------
        data_record: DataRecord
            DataRecord instance
        """

        raise NotImplementedError
